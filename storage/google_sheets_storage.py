from __future__ import annotations

import json
import os
from hashlib import sha256
from collections.abc import Mapping
from typing import Any

import pandas as pd
import streamlit as st

from .base import (
    ALERT_LOG_COLUMNS,
    BENEFIT_COLUMNS,
    CARD_COLUMNS,
    USAGE_COLUMNS,
    StorageBackend,
    prepare_for_write,
    prepare_table,
)


REQUIRED_SERVICE_ACCOUNT_KEYS = {
    "type",
    "project_id",
    "private_key_id",
    "private_key",
    "client_email",
    "client_id",
    "auth_uri",
    "token_uri",
    "auth_provider_x509_cert_url",
    "client_x509_cert_url",
}

TABLE_COLUMNS = {
    "cards": CARD_COLUMNS,
    "benefits": BENEFIT_COLUMNS,
    "usage": USAGE_COLUMNS,
    "alert_log": ALERT_LOG_COLUMNS,
}


def _streamlit_secrets() -> Mapping[str, Any]:
    try:
        import streamlit as st

        return st.secrets
    except Exception:
        return {}


def _secret_value(name: str) -> str:
    secrets = _streamlit_secrets()
    try:
        value = secrets.get(name, "")
    except Exception:
        value = ""
    return str(value).strip() if value is not None else ""


def _service_account_from_secrets() -> dict[str, Any]:
    secrets = _streamlit_secrets()
    try:
        raw_account = secrets.get("gcp_service_account", {})
    except Exception:
        raw_account = {}
    if not raw_account:
        return {}
    return dict(raw_account)


def _service_account_from_env() -> dict[str, Any]:
    raw_json = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON") or os.environ.get("GCP_SERVICE_ACCOUNT_JSON")
    if raw_json:
        return json.loads(raw_json)

    account = {
        "type": os.environ.get("GCP_SERVICE_ACCOUNT_TYPE", ""),
        "project_id": os.environ.get("GCP_PROJECT_ID", ""),
        "private_key_id": os.environ.get("GCP_PRIVATE_KEY_ID", ""),
        "private_key": os.environ.get("GCP_PRIVATE_KEY", ""),
        "client_email": os.environ.get("GCP_CLIENT_EMAIL", ""),
        "client_id": os.environ.get("GCP_CLIENT_ID", ""),
        "auth_uri": os.environ.get("GCP_AUTH_URI", "https://accounts.google.com/o/oauth2/auth"),
        "token_uri": os.environ.get("GCP_TOKEN_URI", "https://oauth2.googleapis.com/token"),
        "auth_provider_x509_cert_url": os.environ.get(
            "GCP_AUTH_PROVIDER_X509_CERT_URL",
            "https://www.googleapis.com/oauth2/v1/certs",
        ),
        "client_x509_cert_url": os.environ.get("GCP_CLIENT_X509_CERT_URL", ""),
    }
    return account if any(account.values()) else {}


def _service_account_info() -> dict[str, Any]:
    account = _service_account_from_secrets() or _service_account_from_env()
    if "private_key" in account and isinstance(account["private_key"], str):
        account["private_key"] = account["private_key"].replace("\\n", "\n")

    missing = sorted(key for key in REQUIRED_SERVICE_ACCOUNT_KEYS if not account.get(key))
    if missing:
        missing_text = ", ".join(missing)
        raise RuntimeError(f"Missing Google service account credential fields: {missing_text}")
    return account


def _credential_fingerprint(account: dict[str, Any]) -> str:
    payload = json.dumps(account, sort_keys=True, default=str)
    return sha256(payload.encode("utf-8")).hexdigest()


@st.cache_resource(show_spinner=False)
def _cached_spreadsheet(
    spreadsheet_id: str,
    spreadsheet_url: str,
    credential_fingerprint: str,
    _account_info: dict[str, Any],
):
    try:
        import gspread
    except ImportError as exc:
        raise RuntimeError(
            "Install gspread and google-auth before using DATA_BACKEND=google_sheets."
        ) from exc

    client = gspread.service_account_from_dict(_account_info)
    if spreadsheet_id:
        return client.open_by_key(spreadsheet_id)
    return client.open_by_url(spreadsheet_url)


@st.cache_data(ttl=60, show_spinner=False)
def _cached_table_bundle(
    spreadsheet_id: str,
    spreadsheet_url: str,
    credential_fingerprint: str,
    _account_info: dict[str, Any],
) -> dict[str, pd.DataFrame]:
    spreadsheet = _cached_spreadsheet(
        spreadsheet_id,
        spreadsheet_url,
        credential_fingerprint,
        _account_info,
    )
    tables = {}
    for table_name, columns in TABLE_COLUMNS.items():
        try:
            worksheet = spreadsheet.worksheet(table_name)
        except Exception as exc:
            if table_name == "alert_log" and exc.__class__.__name__ == "WorksheetNotFound":
                tables[table_name] = prepare_table(pd.DataFrame(columns=columns), columns)
                continue
            raise
        values = worksheet.get_all_values()
        if values:
            tables[table_name] = prepare_table(pd.DataFrame(values[1:], columns=values[0]), columns)
        else:
            tables[table_name] = prepare_table(pd.DataFrame(columns=columns), columns)
    return tables


class GoogleSheetsStorage(StorageBackend):
    def __init__(self, spreadsheet_id: str = "", spreadsheet_url: str = "") -> None:
        self.spreadsheet_id = spreadsheet_id or _secret_value("GOOGLE_SHEET_ID") or os.environ.get("GOOGLE_SHEET_ID", "")
        self.spreadsheet_url = spreadsheet_url or _secret_value("GOOGLE_SHEET_URL") or os.environ.get("GOOGLE_SHEET_URL", "")
        if not self.spreadsheet_id and not self.spreadsheet_url:
            raise RuntimeError("Set GOOGLE_SHEET_ID or GOOGLE_SHEET_URL to use DATA_BACKEND=google_sheets.")
        self._account_info = _service_account_info()
        self._credential_fingerprint = _credential_fingerprint(self._account_info)

    def ensure_data_files(self) -> None:
        return None

    def _open_spreadsheet(self):
        return _cached_spreadsheet(
            self.spreadsheet_id,
            self.spreadsheet_url,
            self._credential_fingerprint,
            self._account_info,
        )

    def _worksheet(self, table_name: str):
        spreadsheet = self._open_spreadsheet()
        try:
            return spreadsheet.worksheet(table_name)
        except Exception as exc:
            if table_name == "alert_log" and exc.__class__.__name__ == "WorksheetNotFound":
                columns = TABLE_COLUMNS[table_name]
                return spreadsheet.add_worksheet(title=table_name, rows=1, cols=len(columns))
            raise

    def read_table(self, table_name: str, columns: list[str]) -> pd.DataFrame:
        tables = _cached_table_bundle(
            self.spreadsheet_id,
            self.spreadsheet_url,
            self._credential_fingerprint,
            self._account_info,
        )
        if table_name in tables:
            return prepare_table(tables[table_name], columns)
        values = self._worksheet(table_name).get_all_values()
        if values:
            return prepare_table(pd.DataFrame(values[1:], columns=values[0]), columns)
        return prepare_table(pd.DataFrame(columns=columns), columns)

    def save_table(self, table_name: str, df: pd.DataFrame, columns: list[str]) -> None:
        try:
            from gspread_dataframe import set_with_dataframe
        except ImportError as exc:
            raise RuntimeError(
                "Install gspread, google-auth, and gspread-dataframe before writing to Google Sheets."
            ) from exc

        worksheet = self._worksheet(table_name)
        prepared = prepare_for_write(df, columns).fillna("")

        # Whole-table writes keep this storage backend simple for a single-user app.
        # Concurrent editing is not supported: the last save wins for the full tab.
        worksheet.clear()
        set_with_dataframe(
            worksheet,
            prepared,
            include_index=False,
            include_column_header=True,
            resize=True,
        )
        _cached_table_bundle.clear()

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from typing import Any

import pandas as pd

from .base import StorageBackend, prepare_table


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


class GoogleSheetsStorage(StorageBackend):
    def __init__(self, spreadsheet_id: str = "", spreadsheet_url: str = "") -> None:
        self.spreadsheet_id = spreadsheet_id or _secret_value("GOOGLE_SHEET_ID") or os.environ.get("GOOGLE_SHEET_ID", "")
        self.spreadsheet_url = spreadsheet_url or _secret_value("GOOGLE_SHEET_URL") or os.environ.get("GOOGLE_SHEET_URL", "")
        if not self.spreadsheet_id and not self.spreadsheet_url:
            raise RuntimeError("Set GOOGLE_SHEET_ID or GOOGLE_SHEET_URL to use DATA_BACKEND=google_sheets.")
        self._spreadsheet = None

    def ensure_data_files(self) -> None:
        return None

    def _client(self):
        try:
            import gspread
        except ImportError as exc:
            raise RuntimeError(
                "Install gspread and google-auth before using DATA_BACKEND=google_sheets."
            ) from exc
        return gspread.service_account_from_dict(_service_account_info())

    def _open_spreadsheet(self):
        if self._spreadsheet is not None:
            return self._spreadsheet

        client = self._client()
        if self.spreadsheet_id:
            self._spreadsheet = client.open_by_key(self.spreadsheet_id)
        else:
            self._spreadsheet = client.open_by_url(self.spreadsheet_url)
        return self._spreadsheet

    def read_table(self, table_name: str, columns: list[str]) -> pd.DataFrame:
        worksheet = self._open_spreadsheet().worksheet(table_name)
        values = worksheet.get_all_values()
        if not values:
            return prepare_table(pd.DataFrame(columns=columns), columns)

        header = values[0]
        rows = values[1:]
        df = pd.DataFrame(rows, columns=header)
        return prepare_table(df, columns)

    def save_table(self, table_name: str, df: pd.DataFrame, columns: list[str]) -> None:
        raise RuntimeError(
            "The Google Sheets backend is read-only in Phase 2. "
            "Switch DATA_BACKEND=local before saving changes."
        )

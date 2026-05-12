from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

from .base import BENEFIT_COLUMNS, CARD_COLUMNS, USAGE_COLUMNS, StorageBackend
from .local_storage import LocalStorage


def _streamlit_secrets() -> Mapping[str, Any]:
    try:
        import streamlit as st

        return st.secrets
    except Exception:
        return {}


def _config_value(name: str) -> str:
    secrets = _streamlit_secrets()
    try:
        value = secrets.get(name, "")
    except Exception:
        value = ""
    if value:
        return str(value).strip()
    return os.environ.get(name, "").strip()


def get_storage(data_dir: Path, backend: str | None = None) -> StorageBackend:
    selected_backend = (backend or _config_value("DATA_BACKEND") or "local").strip().lower()
    if selected_backend in {"", "local", "csv"}:
        return LocalStorage(data_dir)
    if selected_backend in {"google_sheets", "google-sheets", "sheets"}:
        from .google_sheets_storage import GoogleSheetsStorage

        return GoogleSheetsStorage()

    raise ValueError(
        f"Unsupported DATA_BACKEND={selected_backend!r}. "
        "Supported values are local and google_sheets."
    )


__all__ = [
    "BENEFIT_COLUMNS",
    "CARD_COLUMNS",
    "USAGE_COLUMNS",
    "StorageBackend",
    "get_storage",
]

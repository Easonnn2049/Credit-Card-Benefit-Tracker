from __future__ import annotations

from pathlib import Path

import pandas as pd

from .base import (
    ALERT_LOG_COLUMNS,
    BENEFIT_COLUMNS,
    CARD_COLUMNS,
    USAGE_COLUMNS,
    StorageBackend,
    prepare_for_write,
    prepare_table,
)


try:
    import streamlit as st
    from streamlit.runtime import exists as streamlit_runtime_exists
except Exception:  # pragma: no cover - streamlit may be unavailable in non-app tooling.
    st = None

    def streamlit_runtime_exists() -> bool:
        return False


def _read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except pd.errors.EmptyDataError:
        return pd.DataFrame()


if st is not None and streamlit_runtime_exists():

    @st.cache_data(show_spinner=False)
    def _cached_read_csv(path_text: str, modified_ns: int, file_size: int) -> pd.DataFrame:
        return _read_csv(Path(path_text))

else:

    def _cached_read_csv(path_text: str, modified_ns: int, file_size: int) -> pd.DataFrame:
        return _read_csv(Path(path_text))


class LocalStorage(StorageBackend):
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.paths = {
            "cards": self.data_dir / "cards.csv",
            "benefits": self.data_dir / "benefits.csv",
            "usage": self.data_dir / "usage.csv",
            "alert_log": self.data_dir / "alert_log.csv",
        }

    def ensure_data_files(self) -> None:
        self.data_dir.mkdir(exist_ok=True)
        if not self.paths["cards"].exists():
            pd.DataFrame(columns=CARD_COLUMNS).to_csv(self.paths["cards"], index=False)
        if not self.paths["benefits"].exists():
            pd.DataFrame(columns=BENEFIT_COLUMNS).to_csv(self.paths["benefits"], index=False)
        if not self.paths["usage"].exists():
            pd.DataFrame(columns=USAGE_COLUMNS).to_csv(self.paths["usage"], index=False)
        if not self.paths["alert_log"].exists():
            pd.DataFrame(columns=ALERT_LOG_COLUMNS).to_csv(self.paths["alert_log"], index=False)

    def read_table(self, table_name: str, columns: list[str]) -> pd.DataFrame:
        self.ensure_data_files()
        path = self.paths[table_name]
        stat = path.stat()
        df = _cached_read_csv(str(path), stat.st_mtime_ns, stat.st_size)
        if df.empty and not list(df.columns):
            df = pd.DataFrame(columns=columns)
        return prepare_table(df, columns)

    def save_table(self, table_name: str, df: pd.DataFrame, columns: list[str]) -> None:
        self.ensure_data_files()
        prepare_for_write(df, columns).to_csv(self.paths[table_name], index=False)
        clear_cache = getattr(_cached_read_csv, "clear", None)
        if clear_cache is not None:
            clear_cache()

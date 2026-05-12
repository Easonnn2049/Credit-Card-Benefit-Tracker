from __future__ import annotations

from pathlib import Path

import pandas as pd

from .base import (
    BENEFIT_COLUMNS,
    CARD_COLUMNS,
    USAGE_COLUMNS,
    StorageBackend,
    prepare_for_write,
    prepare_table,
)


class LocalStorage(StorageBackend):
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.paths = {
            "cards": self.data_dir / "cards.csv",
            "benefits": self.data_dir / "benefits.csv",
            "usage": self.data_dir / "usage.csv",
        }

    def ensure_data_files(self) -> None:
        self.data_dir.mkdir(exist_ok=True)
        if not self.paths["cards"].exists():
            pd.DataFrame(columns=CARD_COLUMNS).to_csv(self.paths["cards"], index=False)
        if not self.paths["benefits"].exists():
            pd.DataFrame(columns=BENEFIT_COLUMNS).to_csv(self.paths["benefits"], index=False)
        if not self.paths["usage"].exists():
            pd.DataFrame(columns=USAGE_COLUMNS).to_csv(self.paths["usage"], index=False)

    def read_table(self, table_name: str, columns: list[str]) -> pd.DataFrame:
        self.ensure_data_files()
        try:
            df = pd.read_csv(self.paths[table_name])
        except pd.errors.EmptyDataError:
            df = pd.DataFrame(columns=columns)
        return prepare_table(df, columns)

    def save_table(self, table_name: str, df: pd.DataFrame, columns: list[str]) -> None:
        self.ensure_data_files()
        prepare_for_write(df, columns).to_csv(self.paths[table_name], index=False)

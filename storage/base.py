from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


CARD_COLUMNS = [
    "card_id",
    "owner",
    "card_name",
    "issuer",
    "card_version",
    "open_date",
    "annual_fee",
    "renewal_month",
    "status",
    "autopay",
    "notes",
    "source_url",
]
BENEFIT_COLUMNS = [
    "benefit_id",
    "card_id",
    "owner",
    "card_name",
    "benefit_name",
    "benefit_type",
    "category",
    "frequency",
    "cycle_rule",
    "current_cycle",
    "expiration_date",
    "face_value",
    "realistic_value",
    "used_amount",
    "remaining_amount",
    "usage_percent",
    "status",
    "days_until_expiry",
    "priority",
    "include_in_alert",
    "notes",
    "source_url",
    "review_needed",
]
USAGE_COLUMNS = [
    "usage_id",
    "used_date",
    "owner",
    "card_id",
    "benefit_id",
    "benefit_name",
    "cycle_period",
    "used_amount",
    "fully_used",
    "merchant",
    "notes",
]
ALERT_LOG_COLUMNS = [
    "alert_id",
    "alert_type",
    "entity_type",
    "entity_id",
    "card_id",
    "benefit_id",
    "reminder_window",
    "scheduled_for_date",
    "sent_at",
    "recipient_email",
    "status",
    "error_message",
]

NUMERIC_COLUMNS = {
    "annual_fee",
    "face_value",
    "realistic_value",
    "used_amount",
    "remaining_amount",
    "usage_percent",
    "days_until_expiry",
}


def prepare_table(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    prepared = df.copy()
    for column in columns:
        if column not in prepared.columns:
            prepared[column] = ""

    for column in NUMERIC_COLUMNS.intersection(prepared.columns):
        prepared[column] = pd.to_numeric(prepared[column], errors="coerce").fillna(0)

    return prepared[columns].copy()


def prepare_for_write(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    prepared = df.copy()
    for column in columns:
        if column not in prepared.columns:
            prepared[column] = ""
    return prepared[columns].copy()


class StorageBackend(ABC):
    @abstractmethod
    def ensure_data_files(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def read_table(self, table_name: str, columns: list[str]) -> pd.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def save_table(self, table_name: str, df: pd.DataFrame, columns: list[str]) -> None:
        raise NotImplementedError

    def read_cards(self) -> pd.DataFrame:
        return self.read_table("cards", CARD_COLUMNS)

    def read_benefits(self) -> pd.DataFrame:
        return self.read_table("benefits", BENEFIT_COLUMNS)

    def read_usage(self) -> pd.DataFrame:
        return self.read_table("usage", USAGE_COLUMNS)

    def read_alert_log(self) -> pd.DataFrame:
        return self.read_table("alert_log", ALERT_LOG_COLUMNS)

    def save_cards(self, df: pd.DataFrame) -> None:
        self.save_table("cards", df, CARD_COLUMNS)

    def save_benefits(self, df: pd.DataFrame) -> None:
        self.save_table("benefits", df, BENEFIT_COLUMNS)

    def save_usage(self, df: pd.DataFrame) -> None:
        self.save_table("usage", df, USAGE_COLUMNS)

    def save_alert_log(self, df: pd.DataFrame) -> None:
        self.save_table("alert_log", df, ALERT_LOG_COLUMNS)

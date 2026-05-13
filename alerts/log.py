from __future__ import annotations

from datetime import datetime

import pandas as pd

from storage import ALERT_LOG_COLUMNS


SENT_STATUSES = {"sent", "success", "delivered"}


def sent_alert_ids(alert_log: pd.DataFrame) -> set[str]:
    if alert_log.empty or "alert_id" not in alert_log.columns:
        return set()

    log = alert_log.copy()
    if "status" not in log.columns:
        return set(log["alert_id"].dropna().astype(str))

    status = log["status"].fillna("").astype(str).str.strip().str.lower()
    sent = log[status.isin(SENT_STATUSES)]
    return set(sent["alert_id"].dropna().astype(str))


def log_rows_for_alerts(
    benefits: pd.DataFrame,
    annual_fees: pd.DataFrame,
    recipient_email: str,
    status: str,
    error_message: str = "",
    sent_at: datetime | None = None,
) -> pd.DataFrame:
    timestamp = (sent_at or datetime.now()).isoformat(timespec="seconds")
    rows = []

    for _, row in benefits.iterrows():
        rows.append(
            {
                "alert_id": row.get("alert_id", ""),
                "alert_type": row.get("alert_type", ""),
                "entity_type": "benefit",
                "entity_id": row.get("entity_id", row.get("benefit_id", "")),
                "card_id": row.get("card_id", ""),
                "benefit_id": row.get("benefit_id", ""),
                "reminder_window": row.get("reminder_window", ""),
                "scheduled_for_date": row.get("scheduled_for_date", ""),
                "sent_at": timestamp,
                "recipient_email": recipient_email,
                "status": status,
                "error_message": error_message,
            }
        )

    for _, row in annual_fees.iterrows():
        rows.append(
            {
                "alert_id": row.get("alert_id", ""),
                "alert_type": row.get("alert_type", ""),
                "entity_type": "annual_fee",
                "entity_id": row.get("entity_id", row.get("card_id", "")),
                "card_id": row.get("card_id", ""),
                "benefit_id": "",
                "reminder_window": row.get("reminder_window", ""),
                "scheduled_for_date": row.get("scheduled_for_date", ""),
                "sent_at": timestamp,
                "recipient_email": recipient_email,
                "status": status,
                "error_message": error_message,
            }
        )

    return pd.DataFrame(rows, columns=ALERT_LOG_COLUMNS)


def log_rows_for_preview(
    benefits: pd.DataFrame,
    annual_fees: pd.DataFrame,
    recipient_email: str,
    status: str,
    error_message: str = "",
    sent_at: datetime | None = None,
) -> pd.DataFrame:
    return log_rows_for_alerts(benefits, annual_fees, recipient_email, status, error_message, sent_at)

from __future__ import annotations

import pandas as pd


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

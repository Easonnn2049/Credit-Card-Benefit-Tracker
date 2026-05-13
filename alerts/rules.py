from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from hashlib import sha256

import pandas as pd

from .log import sent_alert_ids


BENEFIT_RULES = {
    "monthly": ("benefit_monthly_7d", "7d", 7),
    "quarterly": ("benefit_quarterly_14d", "14d", 14),
    "semiannual": ("benefit_semiannual_30d", "30d", 30),
    "semi-annual": ("benefit_semiannual_30d", "30d", 30),
    "annual": [
        ("benefit_annual_60d", "60d", 60),
        ("benefit_annual_30d", "30d", 30),
    ],
}

ACTIVE_BENEFIT_STATUSES = {"not used", "partially used"}


@dataclass(frozen=True)
class AlertPreview:
    benefits: pd.DataFrame
    annual_fees: pd.DataFrame
    skipped_benefits: pd.DataFrame
    skipped_annual_fees: pd.DataFrame
    run_date: date
    recipient_email: str

    @property
    def benefit_count(self) -> int:
        return len(self.benefits)

    @property
    def annual_fee_count(self) -> int:
        return len(self.annual_fees)

    @property
    def total_remaining_value(self) -> float:
        if self.benefits.empty or "remaining_amount" not in self.benefits.columns:
            return 0.0
        return float(pd.to_numeric(self.benefits["remaining_amount"], errors="coerce").fillna(0).sum())


def _clean(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def _money(value: object) -> float:
    if pd.isna(value) or value == "":
        return 0.0
    if isinstance(value, str):
        value = value.replace("$", "").replace(",", "").strip()
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _date(value: object) -> date | None:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def _alert_id(parts: list[object]) -> str:
    payload = "|".join(_clean(part).lower() for part in parts)
    digest = sha256(payload.encode("utf-8")).hexdigest()[:18]
    return f"alert_{digest}"


def _benefit_rules_for_frequency(frequency: object) -> list[tuple[str, str, int]]:
    text = _clean(frequency).lower().replace("_", "-")
    for key, rule in BENEFIT_RULES.items():
        if key in text:
            if isinstance(rule, list):
                return rule
            return [rule]
    return []


def _action_hint(frequency: object, benefit_type: object, category: object) -> str:
    frequency_text = _clean(frequency).lower()
    benefit_type_text = _clean(benefit_type).lower()
    category_text = _clean(category).lower()

    if "annual" in frequency_text or "free night" in benefit_type_text or "hotel" in category_text:
        return "Plan ahead; this may require booking."
    if any(word in category_text for word in ["dining", "rideshare", "shopping", "entertainment"]):
        return "Check merchant/category requirements before using."
    return "Use before this cycle resets."


def _available_benefits(benefits: pd.DataFrame) -> pd.DataFrame:
    if benefits.empty:
        return benefits.copy()

    df = benefits.copy()
    status = df.get("status", "").fillna("").astype(str).str.strip().str.lower()
    include = df.get("include_in_alert", "").fillna("").astype(str).str.strip().str.lower()
    remaining = pd.to_numeric(df.get("remaining_amount", 0), errors="coerce").fillna(0)
    return df[status.isin(ACTIVE_BENEFIT_STATUSES) & include.eq("yes") & remaining.gt(0)].copy()


def benefit_alert_candidates(benefits: pd.DataFrame, run_date: date, recipient_email: str) -> pd.DataFrame:
    rows = []
    for _, row in _available_benefits(benefits).iterrows():
        expiration = _date(row.get("expiration_date"))
        if not expiration:
            continue

        days_left = (expiration - run_date).days
        for alert_type, reminder_window, target_days in _benefit_rules_for_frequency(row.get("frequency")):
            if days_left != target_days:
                continue

            benefit_id = _clean(row.get("benefit_id"))
            card_id = _clean(row.get("card_id"))
            current_cycle = _clean(row.get("current_cycle"))
            alert_id = _alert_id(
                [
                    alert_type,
                    "benefit",
                    benefit_id,
                    card_id,
                    current_cycle,
                    expiration.isoformat(),
                    reminder_window,
                    recipient_email,
                ]
            )
            rows.append(
                {
                    **row.to_dict(),
                    "alert_id": alert_id,
                    "alert_type": alert_type,
                    "entity_type": "benefit",
                    "entity_id": benefit_id,
                    "reminder_window": reminder_window,
                    "scheduled_for_date": run_date.isoformat(),
                    "due_date": expiration.isoformat(),
                    "days_left": days_left,
                    "display_cycle": _clean(row.get("frequency")),
                    "action_hint": _action_hint(row.get("frequency"), row.get("benefit_type"), row.get("category")),
                }
            )

    return pd.DataFrame(rows)


def annual_fee_date(open_date: object, run_date: date) -> date | None:
    opened = _date(open_date)
    if not opened:
        return None

    year = run_date.year
    while year <= run_date.year + 1:
        try:
            candidate = date(year, opened.month, opened.day)
        except ValueError:
            candidate = date(year, 2, 28)
        if candidate >= run_date:
            return candidate
        year += 1
    return None


def annual_fee_alert_candidates(cards: pd.DataFrame, run_date: date, recipient_email: str) -> pd.DataFrame:
    rows = []
    if cards.empty:
        return pd.DataFrame(rows)

    for _, row in cards.iterrows():
        status = _clean(row.get("status")).lower()
        if status == "closed":
            continue

        annual_fee = _money(row.get("annual_fee"))
        if annual_fee <= 0:
            continue

        fee_date = annual_fee_date(row.get("open_date"), run_date)
        if not fee_date:
            continue

        days_left = (fee_date - run_date).days
        if days_left == 30:
            alert_type = "annual_fee_30d"
            reminder_window = "30d"
        elif days_left == 0:
            alert_type = "annual_fee_due_today"
            reminder_window = "due_today"
        else:
            continue

        card_id = _clean(row.get("card_id"))
        alert_id = _alert_id(
            [
                alert_type,
                "annual_fee",
                card_id,
                fee_date.isoformat(),
                reminder_window,
                recipient_email,
            ]
        )
        rows.append(
            {
                **row.to_dict(),
                "alert_id": alert_id,
                "alert_type": alert_type,
                "entity_type": "annual_fee",
                "entity_id": card_id,
                "reminder_window": reminder_window,
                "scheduled_for_date": run_date.isoformat(),
                "annual_fee_date": fee_date.isoformat(),
                "days_left": days_left,
                "action_hint": "Review whether to keep, downgrade, or cancel before the fee posts.",
            }
        )

    return pd.DataFrame(rows)


def _split_sent(candidates: pd.DataFrame, alert_log: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if candidates.empty:
        return candidates.copy(), candidates.copy()

    sent_ids = sent_alert_ids(alert_log)
    mask = candidates["alert_id"].astype(str).isin(sent_ids)
    return candidates[~mask].copy(), candidates[mask].copy()


def build_alert_preview(
    benefits: pd.DataFrame,
    cards: pd.DataFrame,
    alert_log: pd.DataFrame,
    run_date: date,
    recipient_email: str = "",
) -> AlertPreview:
    benefit_candidates = benefit_alert_candidates(benefits, run_date, recipient_email)
    annual_fee_candidates = annual_fee_alert_candidates(cards, run_date, recipient_email)
    due_benefits, skipped_benefits = _split_sent(benefit_candidates, alert_log)
    due_annual_fees, skipped_annual_fees = _split_sent(annual_fee_candidates, alert_log)

    return AlertPreview(
        benefits=due_benefits.sort_values(["days_left", "due_date", "card_name"]) if not due_benefits.empty else due_benefits,
        annual_fees=due_annual_fees.sort_values(["days_left", "annual_fee_date", "card_name"])
        if not due_annual_fees.empty
        else due_annual_fees,
        skipped_benefits=skipped_benefits,
        skipped_annual_fees=skipped_annual_fees,
        run_date=run_date,
        recipient_email=recipient_email,
    )

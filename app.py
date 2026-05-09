from __future__ import annotations

import base64
from html import escape
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import pandas as pd
import requests
import streamlit as st


APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
CARDS_CSV = DATA_DIR / "cards.csv"
BENEFITS_CSV = DATA_DIR / "benefits.csv"
USAGE_CSV = DATA_DIR / "usage.csv"
ORIGINAL_EXCEL = DATA_DIR / "original_tracker.xlsx"
LIQUID_APP_CSS = APP_DIR / "styles" / "liquid_app.css"
THEME_PREVIEW_CSS = APP_DIR / "styles" / "apple_glass.css"
LIQUID_GLASS_CSS = APP_DIR / "styles" / "liquid_glass.css"

STATUSES = ["Not Used", "Partially Used", "Used"]
EXPIRING_SOON_DAYS = 14

STATUS_COLORS = {
    "Used": ("rgba(209, 250, 229, .62)", "#047857"),
    "Partially Used": ("rgba(254, 243, 199, .68)", "#b45309"),
    "Not Used": ("rgba(255, 255, 255, .52)", "#64748b"),
    "Expiring Soon": ("rgba(255, 228, 230, .66)", "#be4055"),
}

CATEGORY_ICONS = {
    "airline": "✈",
    "travel": "✈",
    "hotel": "▣",
    "dining": "◐",
    "rideshare": "◆",
    "uber": "◆",
    "grocery": "◈",
    "entertainment": "▶",
    "shopping": "◼",
    "other": "●",
}

CARD_ART_COLORS = {
    "amex": ("#a7d8d2", "#174d4a"),
    "american express": ("#a7d8d2", "#174d4a"),
    "chase": ("#bcd7f5", "#123c69"),
    "sapphire": ("#bcd7f5", "#123c69"),
    "united": ("#d8e7ff", "#1c4f8a"),
    "marriott": ("#eadfce", "#5d4037"),
    "hyatt": ("#d7e8f7", "#253b52"),
    "hilton": ("#dcd8ff", "#34236b"),
    "u.s. bank": ("#f5d6d6", "#7a1f2b"),
    "default": ("#ece7db", "#26312a"),
}

CARD_IMAGE_DIR = DATA_DIR / "card_images"
STATUSES = ["Not Used", "Partially Used", "Used", "Ignored"]
STATUS_COLORS["Ignored"] = ("rgba(237, 233, 254, .70)", "#6d5ab8")
CATEGORY_ICONS = {
    "airline": "AIR",
    "travel": "TRV",
    "hotel": "HTL",
    "dining": "DIN",
    "rideshare": "RIDE",
    "uber": "RIDE",
    "grocery": "GRC",
    "entertainment": "ENT",
    "shopping": "SHP",
    "other": "OTH",
}
CATEGORY_COLORS = {
    "airline": ("rgba(219, 234, 254, .72)", "#3157ad"),
    "travel": ("rgba(219, 234, 254, .72)", "#3157ad"),
    "hotel": ("rgba(237, 233, 254, .72)", "#6d5ab8"),
    "dining": ("rgba(254, 243, 199, .70)", "#9a5c0a"),
    "rideshare": ("rgba(209, 250, 229, .66)", "#047857"),
    "uber": ("rgba(209, 250, 229, .66)", "#047857"),
    "grocery": ("rgba(224, 242, 254, .72)", "#03658c"),
    "entertainment": ("rgba(255, 228, 230, .68)", "#a23a50"),
    "shopping": ("rgba(224, 242, 254, .72)", "#2563a8"),
    "other": ("rgba(255, 255, 255, .56)", "#64748b"),
}
CARD_ART_STYLES = {
    "amex gold": ("#d8b45b", "#f4df9b", "#302410", "AMEX", "GOLD"),
    "amex platinum": ("#c8ccd2", "#f5f6f7", "#2a3138", "AMEX", "PLATINUM"),
    "american express gold": ("#d8b45b", "#f4df9b", "#302410", "AMEX", "GOLD"),
    "american express platinum": ("#c8ccd2", "#f5f6f7", "#2a3138", "AMEX", "PLATINUM"),
    "sapphire reserve": ("#1b355d", "#5c8fc9", "#f8fbff", "CHASE", "SAPPHIRE"),
    "sapphire preferred": ("#27577d", "#82b7d8", "#f8fbff", "CHASE", "SAPPHIRE"),
    "united": ("#101f3f", "#376fb0", "#ffffff", "UNITED", "QUEST"),
    "marriott": ("#5a4635", "#c9b295", "#fff7e8", "MARRIOTT", "BONVOY"),
    "hyatt": ("#18344f", "#72a8cf", "#ffffff", "HYATT", "WORLD"),
    "hilton": ("#27316b", "#8b82d8", "#ffffff", "HILTON", "HONORS"),
    "u.s. bank": ("#861c2b", "#d4d7df", "#ffffff", "U.S. BANK", "ALTITUDE"),
    "default": ("#26312a", "#8f9a87", "#ffffff", "CARD", "BENEFITS"),
}

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

NUMERIC_COLUMNS = {
    "annual_fee",
    "face_value",
    "realistic_value",
    "used_amount",
    "remaining_amount",
    "usage_percent",
    "days_until_expiry",
}


def ensure_data_files() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    if not CARDS_CSV.exists():
        pd.DataFrame(columns=CARD_COLUMNS).to_csv(CARDS_CSV, index=False)
    if not BENEFITS_CSV.exists():
        pd.DataFrame(columns=BENEFIT_COLUMNS).to_csv(BENEFITS_CSV, index=False)
    if not USAGE_CSV.exists():
        pd.DataFrame(columns=USAGE_COLUMNS).to_csv(USAGE_CSV, index=False)


def read_csv(path: Path, columns: list[str]) -> pd.DataFrame:
    ensure_data_files()
    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        df = pd.DataFrame(columns=columns)

    for column in columns:
        if column not in df.columns:
            df[column] = ""

    for column in NUMERIC_COLUMNS.intersection(df.columns):
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    return df[columns].copy()


def save_cards(df: pd.DataFrame) -> None:
    for column in CARD_COLUMNS:
        if column not in df.columns:
            df[column] = ""
    df[CARD_COLUMNS].to_csv(CARDS_CSV, index=False)


def save_benefits(df: pd.DataFrame) -> None:
    for column in BENEFIT_COLUMNS:
        if column not in df.columns:
            df[column] = ""
    df[BENEFIT_COLUMNS].to_csv(BENEFITS_CSV, index=False)


def save_usage(df: pd.DataFrame) -> None:
    for column in USAGE_COLUMNS:
        if column not in df.columns:
            df[column] = ""
    df[USAGE_COLUMNS].to_csv(USAGE_CSV, index=False)


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_money(value: object) -> float:
    if pd.isna(value) or value == "":
        return 0.0
    if isinstance(value, str):
        value = value.replace("$", "").replace(",", "").strip()
    try:
        return float(value)
    except ValueError:
        return 0.0


def normalize_date(value: object) -> str:
    if pd.isna(value) or value == "":
        return ""
    if isinstance(value, (int, float)) and 20000 <= value <= 60000:
        parsed = pd.to_datetime(value, unit="D", origin="1899-12-30", errors="coerce")
        return "" if pd.isna(parsed) else parsed.date().isoformat()
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return ""
    return parsed.date().isoformat()


def yes_no(value: object) -> str:
    text = normalize_text(value)
    if text.lower() in {"true", "1", "yes", "y"}:
        return "Yes"
    if text.lower() in {"false", "0", "no", "n"}:
        return "No"
    return text


def normalize_header(column: object) -> str:
    return normalize_text(column).lower().replace(" ", "_").replace("/", "").replace("?", "").replace("-", "_")


def pick_column(columns: list[str], candidates: list[str]) -> str | None:
    normalized = {column.lower().replace(" ", "").replace("_", ""): column for column in columns}
    for candidate in candidates:
        key = candidate.lower().replace(" ", "").replace("_", "")
        if key in normalized:
            return normalized[key]
    for column in columns:
        lowered = column.lower()
        if any(candidate.lower() in lowered for candidate in candidates):
            return column
    return None


def inspect_excel(file_path: Path) -> tuple[dict[str, pd.DataFrame], list[str]]:
    sheets = pd.read_excel(file_path, sheet_name=None)
    summary = []
    for sheet_name, df in sheets.items():
        cols = ", ".join(str(column) for column in df.columns)
        summary.append(f"{sheet_name}: {len(df)} rows; columns: {cols}")
    return sheets, summary


def import_template_workbook(file_path: Path, sheets: dict[str, pd.DataFrame], summary: list[str]) -> dict[str, object]:
    cards_raw = sheets["Cards"].copy()
    master_raw = sheets["Benefits Master"].copy()
    current_raw = sheets["Current Cycle Tracker"].copy()
    usage_raw = sheets["Benefit Usage Log"].copy()

    cards = pd.DataFrame(
        {
            "card_id": cards_raw.get("Card ID", "").map(normalize_text),
            "owner": cards_raw.get("Owner", "").map(normalize_text),
            "card_name": cards_raw.get("Card Name", "").map(normalize_text),
            "issuer": cards_raw.get("Issuer", "").map(normalize_text),
            "card_version": cards_raw.get("Assumed Card Version", "").map(normalize_text),
            "open_date": cards_raw.get("Open Date", "").map(normalize_date),
            "annual_fee": cards_raw.get("Annual Fee", "").map(normalize_money),
            "renewal_month": cards_raw.get("Renewal Month", "").map(normalize_text),
            "status": cards_raw.get("Status", "").map(normalize_text),
            "autopay": cards_raw.get("Autopay?", "").map(yes_no),
            "notes": cards_raw.get("Notes", "").map(normalize_text),
            "source_url": cards_raw.get("Source URL", "").map(normalize_text),
        }
    )
    cards = cards[cards["card_name"] != ""]

    master = pd.DataFrame(
        {
            "benefit_id": master_raw.get("Benefit ID", "").map(normalize_text),
            "card_id": master_raw.get("Card ID", "").map(normalize_text),
            "benefit_type": master_raw.get("Benefit Type", "").map(normalize_text),
            "category": master_raw.get("Category", "").map(normalize_text),
            "realistic_value": master_raw.get("Realistic Value", "").map(normalize_money),
            "source_url": master_raw.get("Source URL", "").map(normalize_text),
            "review_needed": master_raw.get("Review Needed?", "").map(normalize_text),
        }
    )

    current = current_raw.merge(master, how="left", left_on="Benefit ID", right_on="benefit_id")
    benefits = pd.DataFrame(
        {
            "benefit_id": current.get("Benefit ID", "").map(normalize_text),
            "card_id": current.get("card_id", "").map(normalize_text),
            "owner": current.get("Owner", "").map(normalize_text),
            "card_name": current.get("Card Name", "").map(normalize_text),
            "benefit_name": current.get("Benefit Name", "").map(normalize_text),
            "benefit_type": current.get("benefit_type", "").map(normalize_text),
            "category": current.get("category", "").map(normalize_text),
            "frequency": current.get("Frequency", "").map(normalize_text),
            "cycle_rule": current.get("Cycle Rule", "").map(normalize_text),
            "current_cycle": current.get("Current Cycle", "").map(normalize_text),
            "expiration_date": current.get("Expiry Date", "").map(normalize_date),
            "face_value": current.get("Face Value", "").map(normalize_money),
            "realistic_value": current.get("realistic_value", "").map(normalize_money),
            "used_amount": current.get("Amount / Count Used", "").map(normalize_money),
            "remaining_amount": current.get("Remaining", "").map(normalize_money),
            "usage_percent": current.get("Usage %", "").map(normalize_money),
            "status": current.get("Status", "").map(normalize_text),
            "days_until_expiry": current.get("Days Until Expiry", "").map(normalize_money),
            "priority": current.get("Priority", "").map(normalize_text),
            "include_in_alert": current.get("Include in Alert?", "").map(yes_no),
            "notes": current.get("Notes", "").map(normalize_text),
            "source_url": current.get("source_url", "").map(normalize_text),
            "review_needed": current.get("review_needed", "").map(normalize_text),
        }
    )
    benefits = benefits[benefits["benefit_name"] != ""]

    usage = pd.DataFrame(
        {
            "usage_id": usage_raw.get("Usage ID", "").map(normalize_text),
            "used_date": usage_raw.get("Date Used", "").map(normalize_date),
            "owner": usage_raw.get("Owner", "").map(normalize_text),
            "card_id": usage_raw.get("Card ID", "").map(normalize_text),
            "benefit_id": usage_raw.get("Benefit ID", "").map(normalize_text),
            "benefit_name": usage_raw.get("Benefit Name", "").map(normalize_text),
            "cycle_period": usage_raw.get("Cycle Period", "").map(normalize_text),
            "used_amount": usage_raw.get("Amount / Count Used", "").map(normalize_money),
            "fully_used": usage_raw.get("Fully Used?", "").map(yes_no),
            "merchant": usage_raw.get("Merchant", "").map(normalize_text),
            "notes": usage_raw.get("Notes", "").map(normalize_text),
        }
    )
    usage = usage[usage["benefit_name"] != ""]

    save_cards(cards)
    save_benefits(benefits)
    usage[USAGE_COLUMNS].to_csv(USAGE_CSV, index=False)

    return {
        "rows": len(benefits),
        "cards": len(cards),
        "usage": len(usage),
        "summary": summary,
        "mapped": {
            "cards": "Cards sheet",
            "benefits": "Current Cycle Tracker enriched with Benefits Master",
            "usage": "Benefit Usage Log",
        },
        "skipped": ["Dashboard", "Lists", "Sources"],
    }


def import_excel_to_csv(file_path: Path) -> dict[str, object]:
    sheets, summary = inspect_excel(file_path)
    template_sheets = {"Cards", "Benefits Master", "Benefit Usage Log", "Current Cycle Tracker"}
    if template_sheets.issubset(set(sheets)):
        return import_template_workbook(file_path, sheets, summary)

    frames = []
    for sheet_name, df in sheets.items():
        if df.empty:
            continue
        cleaned = df.copy()
        cleaned.columns = [normalize_text(column) or f"Column {index + 1}" for index, column in enumerate(cleaned.columns)]
        cleaned["source_sheet"] = sheet_name
        frames.append(cleaned)

    if not frames:
        return {"rows": 0, "summary": summary, "mapped": {}, "skipped": []}

    combined = pd.concat(frames, ignore_index=True, sort=False)
    columns = list(combined.columns)

    mapped = {
        "owner": pick_column(columns, ["owner", "cardholder", "person", "user", "holder"]),
        "card_name": pick_column(columns, ["card name", "credit card", "card", "product"]),
        "issuer": pick_column(columns, ["issuer", "bank"]),
        "benefit_name": pick_column(columns, ["benefit", "credit", "perk", "offer"]),
        "category": pick_column(columns, ["category", "type"]),
        "cycle": pick_column(columns, ["cycle", "frequency", "period"]),
        "status": pick_column(columns, ["status", "used status"]),
        "benefit_amount": pick_column(columns, ["benefit amount", "amount", "value", "credit amount"]),
        "used_amount": pick_column(columns, ["used amount", "used", "redeemed"]),
        "remaining_amount": pick_column(columns, ["remaining amount", "remaining", "left"]),
        "expiration_date": pick_column(columns, ["expiration", "expiry", "expires", "due date", "deadline"]),
        "notes": pick_column(columns, ["notes", "note", "comments", "comment"]),
    }

    rows = []
    for _, row in combined.iterrows():
        owner = normalize_text(row.get(mapped["owner"])) if mapped["owner"] else ""
        card_name = normalize_text(row.get(mapped["card_name"])) if mapped["card_name"] else ""
        benefit_name = normalize_text(row.get(mapped["benefit_name"])) if mapped["benefit_name"] else ""

        if not card_name and not benefit_name:
            continue

        benefit_amount = normalize_money(row.get(mapped["benefit_amount"])) if mapped["benefit_amount"] else 0.0
        used_amount = normalize_money(row.get(mapped["used_amount"])) if mapped["used_amount"] else 0.0
        remaining_amount = (
            normalize_money(row.get(mapped["remaining_amount"]))
            if mapped["remaining_amount"]
            else max(benefit_amount - used_amount, 0)
        )
        status = normalize_text(row.get(mapped["status"])) if mapped["status"] else ""
        if status not in STATUSES:
            if used_amount <= 0:
                status = "Not Used"
            elif remaining_amount > 0:
                status = "Partially Used"
            else:
                status = "Used"

        rows.append(
            {
                "benefit_id": f"benefit_{uuid4().hex[:10]}",
                "card_id": "",
                "owner": owner,
                "card_name": card_name,
                "benefit_name": benefit_name or "Unnamed benefit",
                "benefit_type": "",
                "category": normalize_text(row.get(mapped["category"])) if mapped["category"] else "",
                "frequency": normalize_text(row.get(mapped["cycle"])) if mapped["cycle"] else "",
                "cycle_rule": "",
                "current_cycle": "",
                "expiration_date": normalize_date(row.get(mapped["expiration_date"])) if mapped["expiration_date"] else "",
                "face_value": benefit_amount,
                "realistic_value": benefit_amount,
                "used_amount": used_amount,
                "remaining_amount": remaining_amount,
                "usage_percent": used_amount / benefit_amount if benefit_amount else 0,
                "status": status,
                "days_until_expiry": "",
                "priority": "",
                "include_in_alert": "Yes",
                "notes": normalize_text(row.get(mapped["notes"])) if mapped["notes"] else "",
                "source_url": "",
                "review_needed": "",
            }
        )

    benefits = pd.DataFrame(rows, columns=BENEFIT_COLUMNS)
    card_rows = []
    if not benefits.empty:
        for _, row in benefits[["owner", "card_name"]].drop_duplicates().iterrows():
            card_id = f"card_{uuid4().hex[:10]}"
            card_rows.append(
                {
                    "card_id": card_id,
                    "owner": row["owner"],
                    "card_name": row["card_name"],
                    "issuer": "",
                    "card_version": "",
                    "open_date": "",
                    "annual_fee": 0,
                    "renewal_month": "",
                    "status": "Active",
                    "autopay": "",
                    "notes": "",
                    "source_url": "",
                }
            )
            benefits.loc[
                (benefits["owner"] == row["owner"]) & (benefits["card_name"] == row["card_name"]),
                "card_id",
            ] = card_id

    cards = pd.DataFrame(card_rows, columns=CARD_COLUMNS)
    save_cards(cards)
    save_benefits(benefits)
    read_csv(USAGE_CSV, USAGE_COLUMNS).to_csv(USAGE_CSV, index=False)

    skipped = [column for column in columns if column not in set(value for value in mapped.values() if value)]
    return {"rows": len(benefits), "summary": summary, "mapped": mapped, "skipped": skipped}


def benefit_status_flags(benefits: pd.DataFrame) -> pd.DataFrame:
    df = benefits.copy()
    today = pd.Timestamp.today().normalize()
    expires = pd.to_datetime(df["expiration_date"], errors="coerce")
    df["days_until_expiration"] = (expires - today).dt.days
    df["cycle_start_date"] = df.apply(cycle_start_date, axis=1)
    starts = pd.to_datetime(df["cycle_start_date"], errors="coerce")
    df["days_until_start"] = (starts - today).dt.days
    df["is_upcoming"] = (
        df["days_until_start"].gt(0)
        & (~df["status"].isin(["Used", "Ignored"]))
    )
    df["is_expiring_soon"] = (
        df["days_until_expiration"].between(0, EXPIRING_SOON_DAYS, inclusive="both")
        & (~df["status"].isin(["Used", "Ignored"]))
        & (~df["is_upcoming"])
    )
    df["needs_action"] = df["status"].isin(["Not Used", "Partially Used"]) & (~df["is_upcoming"])
    df["is_active"] = ~df["status"].isin(["Used", "Ignored"])
    return df


def cycle_start_date(row: pd.Series) -> str:
    current_cycle = clean_display(row.get("current_cycle"), "")
    benefit_name = clean_display(row.get("benefit_name"), "")
    frequency = clean_display(row.get("frequency"), "").lower()
    expiration = pd.to_datetime(row.get("expiration_date"), errors="coerce")
    year = None
    if current_cycle[:4].isdigit():
        year = int(current_cycle[:4])
    elif pd.notna(expiration):
        year = int(expiration.year)
    if not year:
        return ""

    if "H2" in benefit_name or current_cycle.endswith("H2"):
        return f"{year}-07-01"
    if "H1" in benefit_name or current_cycle.endswith("H1"):
        return f"{year}-01-01"
    if "quarter" in frequency or "Q" in current_cycle:
        quarter_match = pd.Series([current_cycle]).str.extract(r"Q([1-4])").iloc[0, 0]
        if pd.notna(quarter_match):
            month = (int(quarter_match) - 1) * 3 + 1
            return f"{year}-{month:02d}-01"
    if "month" in frequency and len(current_cycle) >= 7:
        parsed = pd.to_datetime(f"{current_cycle[:7]}-01", errors="coerce")
        if pd.notna(parsed):
            return parsed.date().isoformat()
    if pd.notna(expiration):
        if "semi" in frequency or "bi" in frequency:
            return f"{year}-07-01" if expiration.month > 6 else f"{year}-01-01"
        return f"{year}-01-01"
    return ""


def inject_styles() -> None:
    if LIQUID_APP_CSS.exists():
        st.markdown(f"<style>{LIQUID_APP_CSS.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def format_amount(value: object) -> str:
    amount = normalize_money(value)
    return f"${amount:,.0f}" if amount == round(amount) else f"${amount:,.2f}"


def clean_display(value: object, fallback: str = "—") -> str:
    text = normalize_text(value)
    return text if text else fallback


def category_icon(category: object) -> str:
    text = normalize_text(category).lower()
    for key, icon in CATEGORY_ICONS.items():
        if key in text:
            return icon
    return CATEGORY_ICONS["other"]


def category_color(category: object) -> tuple[str, str]:
    text = normalize_text(category).lower()
    for key, colors in CATEGORY_COLORS.items():
        if key in text:
            return colors
    return CATEGORY_COLORS["other"]


def title_block(title: str, subtitle: str = "", level: int = 2) -> None:
    subtitle_html = f"<p>{escape(subtitle)}</p>" if subtitle else ""
    st.markdown(
        f"""
        <div class="section-title-block">
            <h{level}>{escape(title)}</h{level}>
            {subtitle_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def load_theme_preview_css() -> None:
    if not THEME_PREVIEW_CSS.exists():
        return
    st.markdown(f"<style>{THEME_PREVIEW_CSS.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def load_liquid_glass_css() -> None:
    if not LIQUID_GLASS_CSS.exists():
        return
    st.markdown(f"<style>{LIQUID_GLASS_CSS.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def preview_metric_card(label: str, value: str, delta: str) -> str:
    return f"""
        <div class="preview-metric">
            <div class="preview-label">{escape(label)}</div>
            <div class="preview-value">{escape(value)}</div>
            <div class="preview-delta">{escape(delta)}</div>
        </div>
    """


def render_theme_concept(concept: dict[str, str]) -> None:
    metrics = [
        ("Remaining", "$428", "Across 9 active credits"),
        ("Used", "$312", "42% of tracked value"),
        ("Due Soon", "3", "Next 14 days"),
        ("Cards", "6", "2 owners tracked"),
    ]
    metric_html = "".join(preview_metric_card(label, value, delta) for label, value, delta in metrics)
    st.markdown(
        f"""
        <div class="theme-preview-shell {escape(concept['class'])}">
            <div class="preview-hero">
                <div>
                    <div class="preview-kicker">{escape(concept['kicker'])}</div>
                    <h2 class="preview-title">{escape(concept['name'])}</h2>
                    <p class="preview-subtitle">{escape(concept['subtitle'])}</p>
                </div>
                <div class="preview-pill">{escape(concept['pill'])}</div>
            </div>
            <div class="preview-metrics">
                {metric_html}
            </div>
            <div class="preview-benefit-card">
                <div class="preview-card-layout">
                    <div class="preview-card-art">
                        <div class="preview-chip"></div>
                        <div>
                            <div class="preview-card-brand">Personal Wallet</div>
                            <div class="preview-card-name">Sapphire Reserve</div>
                        </div>
                    </div>
                    <div>
                        <div class="preview-benefit-header">
                            <div>
                                <div class="preview-benefit-title">$300 Annual Travel Credit</div>
                                <div class="preview-meta">Yuxuan - Chase Sapphire Reserve - Travel - 2026 cycle</div>
                            </div>
                            <div class="preview-pill">$118 left</div>
                        </div>
                        <div class="preview-badges">
                            <span class="preview-status status-used">Used $182</span>
                            <span class="preview-status status-available">Available $118</span>
                            <span class="preview-status status-due">Due Soon</span>
                        </div>
                        <div class="preview-progress-header">
                            <span>Tracked value used</span>
                            <span>63%</span>
                        </div>
                        <div class="preview-progress">
                            <div class="preview-progress-fill"></div>
                        </div>
                        <div class="preview-detail-row">
                            <div class="preview-detail-title">Expandable benefit row preview</div>
                            <div class="preview-detail-text">
                                Annual credit, expires Dec 31. Good for airfare, hotel stays, transit, rideshare, and parking.
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.expander(f"Sample expandable benefit row - {concept['name']}"):
        detail_cols = st.columns([1.2, 1, 1])
        detail_cols[0].metric("Face value", "$300")
        detail_cols[1].metric("Remaining", "$118")
        detail_cols[2].metric("Expires", "Dec 31")
        st.caption("Owner: Yuxuan - Card: Chase Sapphire Reserve - Priority: High - Source: issuer benefit terms")
        st.progress(0.63, text="$182 used of $300")


def show_theme_preview() -> None:
    load_theme_preview_css()
    title_block("UI Theme Preview", "Compare four Apple-inspired dashboard directions before changing the real dashboard.")
    st.markdown(
        """
        <div class="theme-preview-page">
            <p class="theme-preview-intro">
                These are static mock components using the same sample data structure. They do not read, save, or modify your tracker data.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    concepts = [
        {
            "name": "Soft Apple Glass",
            "class": "preview-soft",
            "kicker": "Concept 1",
            "subtitle": "Airy glass panels, warm highlights, and iOS-widget depth for a calm daily dashboard.",
            "pill": "Balanced",
        },
        {
            "name": "Dark Glass / Wallet Style",
            "class": "preview-dark",
            "kicker": "Concept 2",
            "subtitle": "A premium dark wallet surface with high-contrast cards and luminous status chips.",
            "pill": "Premium",
        },
        {
            "name": "Minimal White iOS Dashboard",
            "class": "preview-minimal",
            "kicker": "Concept 3",
            "subtitle": "Crisp white panels, quiet borders, and dense information for fast scanning.",
            "pill": "Practical",
        },
        {
            "name": "Colorful Gradient Glass",
            "class": "preview-colorful",
            "kicker": "Concept 4",
            "subtitle": "Brighter gradient glass with a more personal finance app feel and playful hierarchy.",
            "pill": "Expressive",
        },
    ]

    first_row = st.columns(2)
    second_row = st.columns(2)
    for index, concept in enumerate(concepts):
        with (first_row + second_row)[index]:
            render_theme_concept(concept)

    st.markdown(
        """
        <p class="preview-section-note">
            Choose the direction you like best, and Phase 2 can apply that visual system to the real dashboard while preserving the current app logic.
        </p>
        """,
        unsafe_allow_html=True,
    )


def liquid_metric_card(label: str, value: str, note: str) -> str:
    return f"""
        <div class="liquid-card">
            <div class="liquid-card-label">{escape(label)}</div>
            <div class="liquid-card-value">{escape(value)}</div>
            <div class="liquid-card-note">{escape(note)}</div>
        </div>
    """


def render_liquid_variant(variant: dict[str, str]) -> None:
    metric_html = "".join(
        liquid_metric_card(label, value, note)
        for label, value, note in [
            ("Active Benefits", "18", "9 need action this cycle"),
            ("Expiring Soon", "3", "Next deadline in 6 days"),
            ("Completed", "11", "$312 value captured"),
            ("Value Remaining", "$428", "Across active tracked credits"),
        ]
    )
    st.markdown(
        f"""
        <div class="liquid-page {escape(variant['class'])}">
            <div class="liquid-nav">
                <div class="liquid-nav-brand">
                    <span class="liquid-nav-dot"></span>
                    <span>Benefit Wallet</span>
                </div>
                <div class="liquid-nav-items">
                    <span class="liquid-nav-item active">Dashboard</span>
                    <span class="liquid-nav-item">Cards</span>
                    <span class="liquid-nav-item">Due Soon</span>
                    <span class="liquid-nav-item">Completed</span>
                </div>
            </div>

            <div class="liquid-hero">
                <div>
                    <div class="liquid-kicker">{escape(variant['kicker'])}</div>
                    <h2 class="liquid-title">{escape(variant['name'])}</h2>
                    <p class="liquid-subtitle">{escape(variant['subtitle'])}</p>
                </div>
                <div class="liquid-hero-orb"></div>
            </div>

            <div class="liquid-metrics">
                {metric_html}
            </div>

            <div class="liquid-panel">
                <div class="liquid-benefit-layout">
                    <div class="liquid-credit-art">
                        <div class="liquid-credit-chip"></div>
                        <div>
                            <div class="liquid-credit-bank">Chase</div>
                            <div class="liquid-credit-name">Sapphire Reserve</div>
                        </div>
                    </div>
                    <div>
                        <div class="liquid-panel-top">
                            <div>
                                <div class="liquid-benefit-title">$300 Annual Travel Credit</div>
                                <div class="liquid-meta">Yuxuan - Sapphire Reserve - Travel - 2026 annual cycle</div>
                            </div>
                            <span class="liquid-pill available">$118 left</span>
                        </div>

                        <div class="liquid-pill-row">
                            <span class="liquid-pill available">Available</span>
                            <span class="liquid-pill used">Used $182</span>
                            <span class="liquid-pill due">Due Soon</span>
                        </div>

                        <div class="liquid-subcards">
                            <div class="liquid-subcard">
                                <div class="liquid-subcard-label">Remaining</div>
                                <div class="liquid-subcard-value">$118</div>
                            </div>
                            <div class="liquid-subcard">
                                <div class="liquid-subcard-label">Used Value</div>
                                <div class="liquid-subcard-value">$182</div>
                            </div>
                            <div class="liquid-subcard">
                                <div class="liquid-subcard-label">Expires</div>
                                <div class="liquid-subcard-value">Dec 31</div>
                            </div>
                        </div>

                        <div class="liquid-progress-label">
                            <span>Tracked value used</span>
                            <span>63%</span>
                        </div>
                        <div class="liquid-progress">
                            <div class="liquid-progress-fill"></div>
                        </div>

                        <div class="liquid-benefit-row">
                            <div>
                                <div class="liquid-row-title">Rideshare, parking, hotel, airfare, and transit purchases qualify.</div>
                                <div class="liquid-row-copy">Expandable row preview - frequency annual - priority high - include in alert yes.</div>
                            </div>
                            <div class="liquid-row-action">View</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_liquid_glass_preview() -> None:
    load_liquid_glass_css()
    title_block("Liquid Glass Preview", "Three macOS/iOS-inspired directions using the same sample tracker content.")
    st.caption(
        "Static visual mockups only. This page does not read, save, or modify dashboard data, and the real dashboard is unchanged."
    )

    variants = [
        {
            "name": "Variant A - Tahoe Blue Liquid Glass",
            "class": "tahoe",
            "kicker": "Closest to macOS Tahoe",
            "subtitle": "Blue and cyan blurred environment, bright glass rims, floating liquid panels, and visible reflection gradients.",
        },
        {
            "name": "Variant B - Apple Wallet Glass",
            "class": "wallet",
            "kicker": "Premium finance mode",
            "subtitle": "Dark navy translucent layers, stronger card depth, luminous accents, and high-contrast wallet-style hierarchy.",
        },
        {
            "name": "Variant C - Light Aqua Glass",
            "class": "aqua",
            "kicker": "Daily-use readable mode",
            "subtitle": "White and aqua glass, softer glow, cleaner contrast, and a calmer personal finance dashboard feel.",
        },
    ]

    for variant in variants:
        st.markdown(f'<p class="liquid-variant-caption">{escape(variant["name"])}</p>', unsafe_allow_html=True)
        render_liquid_variant(variant)


def category_badge(category: object) -> str:
    label = clean_display(category, "Other")
    background, color = category_color(label)
    return f'<span class="chip" style="background:{background};color:{color};">{escape(label)}</span>'


def muted_chip(value: object) -> str:
    label = clean_display(value, "")
    if not label:
        return ""
    return f'<span class="chip chip-muted">{escape(label)}</span>'


def card_art_style(card_name: object, issuer: object = "") -> tuple[str, str, str, str, str]:
    haystack = f"{normalize_text(card_name)} {normalize_text(issuer)}".lower()
    for key, style in CARD_ART_STYLES.items():
        if key != "default" and key in haystack:
            return style
    return CARD_ART_STYLES["default"]


def card_image_stem(card: pd.Series) -> str:
    card_id = normalize_text(card.get("card_id"))
    if card_id:
        return card_id
    return normalize_text(card.get("card_name")).lower().replace(" ", "_").replace("/", "_")


def find_card_image(card: pd.Series) -> Path | None:
    CARD_IMAGE_DIR.mkdir(exist_ok=True)
    candidates = [
        card_image_stem(card),
        normalize_text(card.get("card_name")).lower().replace(" ", "_").replace("/", "_"),
    ]
    for stem in [candidate for candidate in candidates if candidate]:
        for extension in [".png", ".jpg", ".jpeg", ".webp", ".avif", ".svg"]:
            path = CARD_IMAGE_DIR / f"{stem}{extension}"
            if path.exists():
                return path
    return None


def save_card_image(card: pd.Series, image_bytes: bytes, extension: str) -> Path:
    CARD_IMAGE_DIR.mkdir(exist_ok=True)
    clean_extension = extension.lower().lstrip(".")
    if clean_extension not in {"png", "jpg", "jpeg", "webp", "svg"}:
        clean_extension = "png"
    path = CARD_IMAGE_DIR / f"{card_image_stem(card)}.{clean_extension}"
    path.write_bytes(image_bytes)
    return path


def download_card_image(card: pd.Series, image_url: str) -> Path:
    parsed = urlparse(image_url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Please use an http or https image URL.")

    response = requests.get(image_url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").lower()
    extension = Path(parsed.path).suffix.lower().lstrip(".")
    if not extension:
        extension = "jpg" if "jpeg" in content_type or "jpg" in content_type else "png"
    if "svg" in content_type:
        extension = "svg"
    if extension not in {"png", "jpg", "jpeg", "webp", "svg"}:
        raise ValueError("That URL does not look like a supported image file.")
    return save_card_image(card, response.content, extension)


def card_image_data_uri(path: Path) -> str:
    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".avif": "image/avif",
        ".svg": "image/svg+xml",
    }
    mime_type = mime_types.get(path.suffix.lower(), "image/png")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def render_card_cue(card: pd.Series) -> None:
    image_path = find_card_image(card)
    if image_path:
        st.markdown(
            f'<img class="card-cue" src="{card_image_data_uri(image_path)}" alt="{escape(clean_display(card.get("card_name"), "Card"))}">',
            unsafe_allow_html=True,
        )
        return

    start, end, text_color, brand, _ = card_art_style(card.get("card_name"), card.get("issuer"))
    st.markdown(
        f"""
        <div class="card-cue-fallback" style="background: linear-gradient(135deg, {start}, {end}); color: {text_color};">
            <span>{escape(brand)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_card_image_manager(cards: pd.DataFrame) -> None:
    st.subheader("Card Images")
    st.caption("Upload card art or paste a direct image URL. Images are cached locally in data/card_images.")
    if cards.empty:
        st.info("Add or import cards before adding images.")
        return

    card_options = {
        f"{row.owner} - {row.card_name}": pd.Series(row._asdict())
        for row in cards.itertuples(index=False)
        if normalize_text(row.card_name)
    }
    selected_label = st.selectbox("Card", list(card_options.keys()), key="card_image_card_select")
    selected_card = card_options[selected_label]
    existing = find_card_image(selected_card)
    if existing:
        st.image(str(existing), caption=f"Current image: {existing.name}", width=320)
    else:
        st.info("No local image yet. The app is using its built-in card-art fallback.")

    uploaded = st.file_uploader("Upload image", type=["png", "jpg", "jpeg", "webp"], key="card_image_upload")
    if uploaded is not None:
        extension = Path(uploaded.name).suffix or ".png"
        saved = save_card_image(selected_card, uploaded.getvalue(), extension)
        st.success(f"Saved {saved.name}")
        st.rerun()

    image_url = st.text_input("Or paste a direct image URL", placeholder="https://example.com/card.png")
    if st.button("Download image from URL", type="primary"):
        if not image_url.strip():
            st.warning("Paste an image URL first.")
        else:
            try:
                saved = download_card_image(selected_card, image_url.strip())
                st.success(f"Downloaded {saved.name}")
                st.rerun()
            except Exception as exc:
                st.error(f"Could not download image: {exc}")


def status_badge(status: object, expiring_soon: bool = False) -> str:
    current_status = clean_display(status, "Not Used")
    label = "Expiring Soon" if expiring_soon and current_status not in ["Used", "Ignored"] else current_status
    background, color = STATUS_COLORS.get(label, STATUS_COLORS["Not Used"])
    return f'<span class="badge" style="background:{background};color:{color};">{escape(label)}</span>'


def due_text_from_days(days: object) -> str:
    if pd.isna(days):
        return "No due date"
    if days < 0:
        return "Past due"
    if days == 0:
        return "Due today"
    return f"Due in {int(days)} days"


def date_label(value: object) -> str:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return ""
    return f"{parsed.strftime('%b')} {parsed.day}"


def next_membership_fee_label(card: pd.Series) -> str:
    annual_fee = normalize_money(card.get("annual_fee"))
    if annual_fee <= 0:
        return "No annual fee"

    open_date = pd.to_datetime(card.get("open_date"), errors="coerce")
    if pd.isna(open_date):
        return "Fee date not set"

    today = pd.Timestamp.today().date()
    fee_date = today.replace(month=int(open_date.month), day=int(open_date.day))
    if fee_date <= today:
        fee_date = fee_date.replace(year=fee_date.year + 1)

    days = (fee_date - today).days
    return f"Annual fee in {days} days ({fee_date.strftime('%b')} {fee_date.day})"


def benefit_summary_label(row: pd.Series) -> str:
    name = clean_display(row.get("benefit_name"))
    status = clean_display(row.get("status"), "Not Used")
    upcoming = bool(row.get("is_upcoming", False))
    start_label = date_label(row.get("cycle_start_date"))
    due_text = f"Starts {start_label}" if upcoming and start_label else due_text_from_days(row.get("days_until_expiration"))
    face_value = normalize_money(row.get("face_value"))
    used_amount = normalize_money(row.get("used_amount"))
    remaining = max(face_value - used_amount, 0)
    progress = int(min(max((used_amount / face_value) * 100 if face_value else 0, 0), 100))

    if upcoming:
        label = ":gray[**[Upcoming]**]"
    elif status == "Used":
        label = ":green[**[Completed]**]"
    elif status == "Ignored":
        label = ":violet[**[Ignored]**]"
    elif bool(row.get("is_expiring_soon", False)):
        label = ":red[**[Due Soon]**]"
    elif status == "Not Used":
        label = ":gray[**[Unused]**]"
    elif status == "Partially Used":
        label = ":orange[**[Partial]**]"
    else:
        label = f":blue[**[{status}]**]"

    return f"{label} **{name} · {format_amount(remaining)}**  \n:gray[{due_text} · {progress}% used]"


def benefit_summary_strip(row: pd.Series, expiring: bool) -> str:
    status = clean_display(row.get("status"), "Not Used")
    if expiring and status not in ["Used", "Ignored"]:
        background, color = STATUS_COLORS["Expiring Soon"]
        label = "Expiring soon"
    else:
        background, color = STATUS_COLORS.get(status, STATUS_COLORS["Not Used"])
        label = status

    return f"""
    <div style="
        border-left: 4px solid {color};
        background: {background};
        color: {color};
        border-radius: 8px;
        padding: 8px 10px;
        margin-bottom: 10px;
        font-weight: 800;
    ">
        {escape(label)} / {escape(clean_display(row.get("benefit_name")))}
    </div>
    """


def append_usage_record(benefit: pd.Series, amount_used: float, fully_used: bool, note: str = "Logged from benefit status update") -> None:
    if amount_used <= 0:
        return

    usage = read_csv(USAGE_CSV, USAGE_COLUMNS)
    today = pd.Timestamp.today().date().isoformat()
    record = pd.DataFrame(
        [
            {
                "usage_id": f"usage_{uuid4().hex[:10]}",
                "used_date": today,
                "owner": clean_display(benefit.get("owner"), ""),
                "card_id": clean_display(benefit.get("card_id"), ""),
                "benefit_id": clean_display(benefit.get("benefit_id"), ""),
                "benefit_name": clean_display(benefit.get("benefit_name"), ""),
                "cycle_period": clean_display(benefit.get("current_cycle"), ""),
                "used_amount": amount_used,
                "fully_used": "Yes" if fully_used else "No",
                "merchant": "",
                "notes": note,
            }
        ],
        columns=USAGE_COLUMNS,
    )
    save_usage(pd.concat([usage, record], ignore_index=True))


def sync_usage_log_from_benefits() -> int:
    benefits = read_csv(BENEFITS_CSV, BENEFIT_COLUMNS)
    usage = read_csv(USAGE_CSV, USAGE_COLUMNS)
    new_records = []

    for _, benefit in benefits.iterrows():
        used_amount = normalize_money(benefit.get("used_amount"))
        if used_amount <= 0:
            continue

        benefit_id = clean_display(benefit.get("benefit_id"), "")
        cycle_period = clean_display(benefit.get("current_cycle"), "")
        existing = usage[
            (usage["benefit_id"].astype(str) == benefit_id)
            & (usage["cycle_period"].astype(str).fillna("") == cycle_period)
        ]
        logged_amount = existing["used_amount"].apply(normalize_money).sum() if not existing.empty else 0.0
        missing_amount = used_amount - logged_amount
        if missing_amount <= 0.01:
            continue

        fully_used = clean_display(benefit.get("status"), "Not Used") == "Used"
        new_records.append(
            {
                "usage_id": f"usage_{uuid4().hex[:10]}",
                "used_date": pd.Timestamp.today().date().isoformat(),
                "owner": clean_display(benefit.get("owner"), ""),
                "card_id": clean_display(benefit.get("card_id"), ""),
                "benefit_id": benefit_id,
                "benefit_name": clean_display(benefit.get("benefit_name"), ""),
                "cycle_period": cycle_period,
                "used_amount": missing_amount,
                "fully_used": "Yes" if fully_used else "No",
                "merchant": "",
                "notes": "Backfilled from current benefit status",
            }
        )

    if new_records:
        save_usage(pd.concat([usage, pd.DataFrame(new_records, columns=USAGE_COLUMNS)], ignore_index=True))
    return len(new_records)


def update_benefit_status(benefit_id: str, status: str, used_amount: float | None = None) -> None:
    benefits = read_csv(BENEFITS_CSV, BENEFIT_COLUMNS)
    match = benefits["benefit_id"].astype(str) == str(benefit_id)
    if not match.any():
        st.error("Could not find that benefit in the local CSV.")
        return

    existing = benefits.loc[match].iloc[0].copy()
    face_value = normalize_money(existing.get("face_value"))
    previous_used_amount = normalize_money(existing.get("used_amount"))
    if used_amount is None:
        if status == "Used":
            used_amount = face_value
        elif status == "Not Used":
            used_amount = 0.0
        elif status == "Ignored":
            used_amount = normalize_money(benefits.loc[match, "used_amount"].iloc[0])
        else:
            current = normalize_money(benefits.loc[match, "used_amount"].iloc[0])
            used_amount = current if current > 0 else min(face_value / 2, face_value)

    used_amount = max(float(used_amount), 0.0)
    if face_value and status != "Ignored":
        if used_amount >= face_value:
            status = "Used"
        elif used_amount <= 0:
            status = "Not Used"
        else:
            status = "Partially Used"
    remaining_amount = max(face_value - used_amount, 0.0)
    usage_percent = used_amount / face_value if face_value else 0.0

    benefits.loc[match, "status"] = status
    benefits.loc[match, "used_amount"] = used_amount
    benefits.loc[match, "remaining_amount"] = remaining_amount
    benefits.loc[match, "usage_percent"] = usage_percent
    save_benefits(benefits)

    usage_delta = used_amount - previous_used_amount
    if status in ["Used", "Partially Used"] and usage_delta > 0:
        append_usage_record(
            benefits.loc[match].iloc[0],
            usage_delta,
            status == "Used",
        )

    st.toast(f"Updated to {status}")
    st.rerun()


def render_card_art(card: pd.Series, benefit_count: int) -> None:
    image_path = find_card_image(card)
    if image_path:
        st.image(str(image_path), use_container_width=True)
        return

    start, end, text_color, brand, product = card_art_style(card.get("card_name"), card.get("issuer"))
    st.markdown(
        f"""
        <div class="card-art" style="background: linear-gradient(135deg, {start}, {end}); color: {text_color};">
            <div style="display:flex; justify-content:space-between; align-items:flex-start;">
                <div class="card-brand">{escape(brand)}</div>
                <div class="card-chip"></div>
            </div>
            <div>
                <div class="card-product">{escape(product)}</div>
                <div style="font-weight:700; margin-top:4px;">{escape(clean_display(card.get("card_name")))}</div>
            </div>
            <div class="card-owner">{escape(clean_display(card.get("owner"), "Unassigned"))} / {benefit_count} benefits</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_benefit_tile(
    row: pd.Series,
    key_prefix: str,
    quick_actions_layout: str = "horizontal",
    show_card_cue: bool = False,
) -> None:
    expiring = bool(row.get("is_expiring_soon", False))
    upcoming = bool(row.get("is_upcoming", False))
    due = clean_display(row.get("expiration_date"))
    benefit_id = clean_display(row.get("benefit_id"), "")
    face_value = normalize_money(row.get("face_value"))
    used_amount = normalize_money(row.get("used_amount"))
    remaining_amount = max(face_value - used_amount, 0)
    progress_percent = int(min(max((used_amount / face_value) * 100 if face_value else 0, 0), 100))
    status = clean_display(row.get("status"), "Not Used")
    days = row.get("days_until_expiration")
    start_label = date_label(row.get("cycle_start_date"))
    days_text = f"Starts {start_label}" if upcoming and start_label else due_text_from_days(days)
    deadline_class = "upcoming" if upcoming else "hidden" if status == "Ignored" else "done" if status == "Used" else "soon" if expiring else ""
    category = clean_display(row.get("category"), "Other")
    frequency = clean_display(row.get("frequency"), "")
    read_only_progress = ""
    if status in ["Used", "Ignored"]:
        read_only_progress = f"""
              <div class="progress-shell"><div class="progress-fill" style="width:{progress_percent}%;"></div></div>
              <div class="mini-grid">
                <div class="mini-stat"><div class="mini-label">Used</div><div class="mini-value">{format_amount(used_amount)}</div></div>
                <div class="mini-stat"><div class="mini-label">Left</div><div class="mini-value">{format_amount(remaining_amount)}</div></div>
                <div class="mini-stat"><div class="mini-label">Progress</div><div class="mini-value">{progress_percent}%</div></div>
              </div>
        """

    expander_host = st
    if status not in ["Used", "Ignored"] and not upcoming:
        if quick_actions_layout == "vertical":
            if show_card_cue:
                cue_col, title_col, action_col = st.columns([0.85, 3.75, 1.35], vertical_alignment="top")
                with cue_col:
                    render_card_cue(row)
            else:
                title_col, action_col = st.columns([4.6, 1.35], vertical_alignment="top")
            expander_host = title_col
            with action_col:
                if st.button("Used", key=f"{key_prefix}_{benefit_id}_quick_used", type="primary", use_container_width=True):
                    update_benefit_status(benefit_id, "Used")
                if st.button("Ignore", key=f"{key_prefix}_{benefit_id}_quick_ignore", use_container_width=True):
                    update_benefit_status(benefit_id, "Ignored")
        else:
            title_col, used_col, ignore_col = st.columns([7, 0.85, 0.85], vertical_alignment="top")
            expander_host = title_col
            if used_col.button("Used", key=f"{key_prefix}_{benefit_id}_quick_used", type="primary", use_container_width=True):
                update_benefit_status(benefit_id, "Used")
            if ignore_col.button("Ignore", key=f"{key_prefix}_{benefit_id}_quick_ignore", use_container_width=True):
                update_benefit_status(benefit_id, "Ignored")

    with expander_host.expander(benefit_summary_label(row), expanded=False):
        st.markdown(
            f"""
            <div class="benefit-tile {'upcoming' if upcoming else ''}">
              <div class="benefit-topline">
                <div>
                  <div class="benefit-title">{escape(clean_display(row.get("benefit_name")))}</div>
                  <div class="benefit-meta">
                    {category_badge(category)}
                    {muted_chip(frequency)}
                    <span class="chip chip-muted">{format_amount(remaining_amount)} left</span>
                  </div>
                </div>
                <div class="deadline {deadline_class}">
                    <div>{escape(days_text)}</div>
                    <div style="font-size:.68rem; font-weight:600; opacity:.78; margin-top:2px;">{escape(due)}</div>
                </div>
              </div>
              {read_only_progress}
            </div>
            """,
            unsafe_allow_html=True,
        )

        if upcoming:
            st.info("This benefit has not reached its start window yet. Usage actions will unlock when the cycle starts.")
        elif status == "Used":
            st.success("Completed benefit shown because completed/ignored items are visible.")
            st.caption("This benefit is read-only while completed. Reopen it only if you need to track it again.")
            if st.button("Reopen as not used", key=f"{key_prefix}_{benefit_id}_restore", use_container_width=True):
                update_benefit_status(benefit_id, "Not Used")
        elif status == "Ignored":
            st.warning("Hidden benefit shown because completed/ignored items are visible.")
            st.caption("This benefit is read-only while hidden. Reopen it only if it becomes relevant again.")
            if st.button("Reopen as not used", key=f"{key_prefix}_{benefit_id}_restore", use_container_width=True):
                update_benefit_status(benefit_id, "Not Used")
        else:
            slider_reset_key = f"{key_prefix}_{benefit_id}_slider_reset_token"
            slider_token = st.session_state.get(slider_reset_key, 0)
            slider_key = f"{key_prefix}_{benefit_id}_slider_value_{slider_token}"
            if face_value > 0:
                amount = st.slider(
                    "Used amount",
                    min_value=0.0,
                    max_value=float(face_value),
                    value=float(min(used_amount, face_value)),
                    step=1.0 if face_value >= 10 else 0.5,
                    key=slider_key,
                )
            else:
                amount = st.number_input(
                    "Used amount",
                    min_value=0.0,
                    value=float(used_amount),
                    step=1.0,
                    key=slider_key,
                )

            preview_remaining = max(face_value - amount, 0)
            preview_status = "Used" if face_value and amount >= face_value else "Not Used" if amount <= 0 else "Partially Used"
            preview_progress = int(min(max((amount / face_value) * 100 if face_value else 0, 0), 100))
            st.markdown(
                f"""
                <div class="slider-summary">
                    {format_amount(amount)} used · {format_amount(preview_remaining)} left · {preview_progress}% used · saves as {escape(preview_status)}
                </div>
                """,
                unsafe_allow_html=True,
            )

            action_cols = st.columns([1, 1, 1, 1])
            if action_cols[0].button("Save slider", key=f"{key_prefix}_{benefit_id}_slider_save", type="primary", use_container_width=True):
                update_benefit_status(benefit_id, preview_status, amount)
            if action_cols[1].button("Mark used", key=f"{key_prefix}_{benefit_id}_used", use_container_width=True):
                update_benefit_status(benefit_id, "Used")
            if action_cols[2].button("Reset", key=f"{key_prefix}_{benefit_id}_reset", use_container_width=True):
                st.session_state[slider_reset_key] = slider_token + 1
                update_benefit_status(benefit_id, "Not Used")
            if action_cols[3].button("Hide", key=f"{key_prefix}_{benefit_id}_ignore", use_container_width=True):
                update_benefit_status(benefit_id, "Ignored")

        notes = clean_display(row.get("notes"), "")
        source = clean_display(row.get("source_url"), "")
        if notes or source:
            st.divider()
            if notes:
                st.caption(notes)
            if source:
                st.link_button("Source", source)


def show_importer() -> None:
    title_block(
        "Import Existing Excel Tracker",
        "Upload your existing tracker once. The app preserves the original file and creates local CSV files for daily use.",
        level=3,
    )
    uploaded = st.file_uploader("Excel file", type=["xlsx", "xlsm", "xls"])
    if uploaded is not None:
        DATA_DIR.mkdir(exist_ok=True)
        ORIGINAL_EXCEL.write_bytes(uploaded.getbuffer())
        result = import_excel_to_csv(ORIGINAL_EXCEL)
        st.success(f"Imported {result['rows']} benefit rows from Excel.")
        with st.expander("Detected sheets and columns", expanded=True):
            for line in result["summary"]:
                st.write(line)
        with st.expander("Column mapping"):
            st.json(result["mapped"])
        if result["skipped"]:
            with st.expander("Skipped columns"):
                st.write(", ".join(result["skipped"]))
        st.rerun()


def show_dashboard(benefits: pd.DataFrame) -> None:
    title_block("Dashboard")
    if benefits.empty:
        st.info("No benefits yet. Import your Excel tracker or add a benefit manually.")
        return

    flagged = benefit_status_flags(benefits)
    active = flagged[flagged["is_active"]]
    hidden = flagged[~flagged["is_active"]]
    needs_action = active[active["needs_action"]]
    expiring = active[active["is_expiring_soon"]]
    used = flagged[flagged["status"] == "Used"]
    ignored = flagged[flagged["status"] == "Ignored"]
    remaining_value = active["remaining_amount"].apply(normalize_money).sum()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Active benefits", len(active))
    col2.metric("Expiring soon", len(expiring))
    col3.metric("Completed", len(used))
    col4.metric("Value remaining", format_amount(remaining_value))

    show_hidden = st.toggle("Show completed and ignored in main views", value=False)
    browse_data = flagged if show_hidden else active

    dashboard_view = st.radio(
        "Dashboard view",
        ["Home", "Cards", "Categories", "Completed / Hidden"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if dashboard_view == "Home":
        show_home_view(active, expiring, needs_action)
    elif dashboard_view == "Cards":
        show_by_card_view(browse_data)
    elif dashboard_view == "Categories":
        show_by_category_view(browse_data)
    else:
        show_completed_hidden_view(hidden)


def show_home_view(active: pd.DataFrame, expiring: pd.DataFrame, needs_action: pd.DataFrame) -> None:
    title_block("Benefits to use next", level=3)

    monthly_not_used = active[
        (active["status"] == "Not Used")
        & (active["frequency"].astype(str).str.lower() == "monthly")
        & (~active["is_upcoming"])
    ]
    if monthly_not_used.empty:
        monthly_not_used = active[(active["status"] == "Not Used") & (~active["is_upcoming"])]

    partial = active[(active["status"] == "Partially Used") & (~active["is_upcoming"])]

    lane1, lane2, lane3 = st.columns(3)
    with lane1:
        show_priority_lane("Expiring soon", expiring.sort_values(["expiration_date", "priority"]).head(6), "home_expiring")
    with lane2:
        show_priority_lane("Not used this month", monthly_not_used.sort_values(["expiration_date", "priority"]).head(6), "home_monthly")
    with lane3:
        show_priority_lane("Partially used", partial.sort_values(["expiration_date", "priority"]).head(6), "home_partial")

    if needs_action.empty:
        st.success("No active benefits need attention right now.")


def show_priority_lane(title: str, benefits: pd.DataFrame, key_prefix: str) -> None:
    st.markdown(f"#### {title}")
    if benefits.empty:
        st.info("Nothing here.")
        return
    for index, (_, benefit) in enumerate(benefits.iterrows()):
        render_benefit_tile(
            benefit,
            f"{key_prefix}_{index}",
            quick_actions_layout="vertical",
            show_card_cue=True,
        )


def show_by_card_view(flagged: pd.DataFrame) -> None:
    st.caption("Browse benefits under each card. Use the quick buttons to update status without opening the raw editor.")
    if flagged.empty:
        st.info("No active benefits to show. Use the toggle above or open Completed / Hidden.")
        return
    cards = read_csv(CARDS_CSV, CARD_COLUMNS)
    all_benefits = benefit_status_flags(read_csv(BENEFITS_CSV, BENEFIT_COLUMNS))
    with st.expander("Manage card images", expanded=False):
        show_card_image_manager(cards)

    if cards.empty:
        cards = flagged[["owner", "card_name"]].drop_duplicates().copy()
        cards["issuer"] = ""
        cards["card_id"] = ""

    owners = ["All owners"] + sorted([owner for owner in flagged["owner"].dropna().unique() if normalize_text(owner)])
    selected_owner = st.selectbox("Owner", owners, key="by_card_owner_filter")
    visible_cards = cards.copy()
    if selected_owner != "All owners":
        visible_cards = visible_cards[visible_cards["owner"] == selected_owner]

    for _, card in visible_cards.iterrows():
        card_benefits = flagged[
            (flagged["card_name"] == card.get("card_name"))
            & (flagged["owner"].fillna("") == normalize_text(card.get("owner")))
        ]
        all_card_benefits = all_benefits[
            (all_benefits["card_name"] == card.get("card_name"))
            & (all_benefits["owner"].fillna("") == normalize_text(card.get("owner")))
        ]
        if card_benefits.empty:
            continue

        with st.container(border=True):
            left, right = st.columns([1, 2.2])
            with left:
                render_card_art(card, len(card_benefits))
                used_count = int((card_benefits["status"] == "Used").sum())
                done_count = int(all_card_benefits["status"].isin(["Used", "Ignored"]).sum())
                total_count = max(len(all_card_benefits), 1)
                st.progress(done_count / total_count, text=f"{done_count}/{total_count} complete or hidden")
            with right:
                expiring_count = int(card_benefits["is_expiring_soon"].sum())
                tracked_card_benefits = all_card_benefits[all_card_benefits["status"] != "Ignored"]
                active_count = int(tracked_card_benefits["is_active"].sum()) if "is_active" in tracked_card_benefits else len(card_benefits)
                remaining_value = tracked_card_benefits["remaining_amount"].apply(normalize_money).sum()
                used_value = tracked_card_benefits["used_amount"].apply(normalize_money).sum()
                total_value = tracked_card_benefits["face_value"].apply(normalize_money).sum()
                value_progress = used_value / total_value if total_value else 0
                st.subheader(clean_display(card.get("card_name")))
                st.caption(
                    f"{clean_display(card.get('owner'), 'Unassigned')} · "
                    f"{clean_display(card.get('issuer'), 'Issuer unknown')} · "
                    f"{expiring_count} expiring soon · "
                    f"{next_membership_fee_label(card)}"
                )
                summary_cols = st.columns(3)
                summary_cols[0].metric("Active", active_count)
                summary_cols[1].metric("Remaining", format_amount(remaining_value))
                summary_cols[2].metric("Used value", format_amount(used_value))
                st.progress(min(max(value_progress, 0), 1), text=f"{int(value_progress * 100)}% of tracked value used")
                with st.expander("Show benefits", expanded=expiring_count > 0):
                    for _, benefit in card_benefits.sort_values(["status", "expiration_date", "benefit_name"]).iterrows():
                        render_benefit_tile(benefit, f"card_{normalize_text(card.get('card_id')) or normalize_text(card.get('card_name'))}")


def show_by_category_view(flagged: pd.DataFrame) -> None:
    st.caption("Scan across cards by benefit category.")
    if flagged.empty:
        st.info("No active benefits to show. Use the toggle above or open Completed / Hidden.")
        return
    category_order = ["Dining", "Rideshare", "Travel", "Hotel", "Airline", "Shopping", "Entertainment", "Other"]
    categories = sorted([category for category in flagged["category"].dropna().unique() if normalize_text(category)])
    ordered = [category for category in category_order if category in categories]
    ordered.extend([category for category in categories if category not in ordered])

    for category in ordered:
        group = flagged[flagged["category"] == category]
        if group.empty:
            continue
        icon = category_icon(category)
        used_count = int((group["status"] == "Used").sum())
        with st.container(border=True):
            st.markdown(
                f'<div class="category-chip"><span>{icon}</span><span>{escape(category)}</span></div>',
                unsafe_allow_html=True,
            )
            cols = st.columns(3)
            cols[0].metric("Needs action", int(group["needs_action"].sum()))
            cols[1].metric("Expiring", int(group["is_expiring_soon"].sum()))
            cols[2].metric("Used", used_count)

            benefit_cols = st.columns(2)
            for index, (_, benefit) in enumerate(group.sort_values(["status", "expiration_date", "card_name"]).iterrows()):
                with benefit_cols[index % 2]:
                    st.caption(f"{clean_display(benefit.get('owner'))} · {clean_display(benefit.get('card_name'))}")
                    render_benefit_tile(benefit, f"cat_{normalize_text(category)}_{index}")


def show_action_view(needs_action: pd.DataFrame, expiring: pd.DataFrame) -> None:
    left, right = st.columns(2)
    with left:
        st.subheader("Expiring Soon")
        if expiring.empty:
            st.info("Nothing is expiring soon.")
        for index, (_, benefit) in enumerate(expiring.sort_values(["expiration_date", "priority"]).iterrows()):
            render_benefit_tile(benefit, f"expiring_{index}")

    with right:
        st.subheader("Still Needs Action")
        if needs_action.empty:
            st.info("Everything is marked used.")
        for index, (_, benefit) in enumerate(needs_action.sort_values(["priority", "expiration_date"]).head(12).iterrows()):
            render_benefit_tile(benefit, f"action_{index}")


def show_completed_hidden_view(hidden: pd.DataFrame) -> None:
    st.caption("Completed and ignored benefits stay recoverable here.")
    if hidden.empty:
        st.info("No completed or ignored benefits yet.")
        return

    completed = hidden[hidden["status"] == "Used"]
    ignored = hidden[hidden["status"] == "Ignored"]
    completed_tab, ignored_tab = st.tabs([f"Completed ({len(completed)})", f"Ignored ({len(ignored)})"])
    with completed_tab:
        for index, (_, benefit) in enumerate(completed.sort_values(["card_name", "benefit_name"]).iterrows()):
            render_benefit_tile(benefit, f"completed_{index}")
    with ignored_tab:
        for index, (_, benefit) in enumerate(ignored.sort_values(["card_name", "benefit_name"]).iterrows()):
            render_benefit_tile(benefit, f"ignored_{index}")


def show_edit_benefits(benefits: pd.DataFrame) -> None:
    title_block("Edit Benefits", "Make direct changes to tracked benefit rows.")
    if benefits.empty:
        st.info("No benefits to edit yet.")
        return

    editable = benefits.copy()
    editable["expiration_date"] = pd.to_datetime(editable["expiration_date"], errors="coerce")

    edited = st.data_editor(
        editable,
        column_config={
            "benefit_id": None,
            "card_id": None,
            "status": st.column_config.SelectboxColumn("status", options=STATUSES),
            "expiration_date": st.column_config.DateColumn("expiration_date", format="YYYY-MM-DD"),
            "face_value": st.column_config.NumberColumn("face_value", min_value=0.0, step=1.0),
            "realistic_value": st.column_config.NumberColumn("realistic_value", min_value=0.0, step=1.0),
            "used_amount": st.column_config.NumberColumn("used_amount", min_value=0.0, step=1.0),
            "remaining_amount": st.column_config.NumberColumn("remaining_amount", min_value=0.0, step=1.0),
            "usage_percent": st.column_config.NumberColumn("usage_percent", min_value=0.0, max_value=1.0, step=0.05),
            "include_in_alert": st.column_config.SelectboxColumn("include_in_alert", options=["Yes", "No"]),
            "priority": st.column_config.SelectboxColumn("priority", options=["High", "Medium", "Low", ""]),
        },
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
    )
    if st.button("Save benefit changes", type="primary"):
        edited = edited.copy()
        edited["expiration_date"] = pd.to_datetime(edited["expiration_date"], errors="coerce").dt.date
        edited["expiration_date"] = edited["expiration_date"].apply(lambda value: value.isoformat() if pd.notna(value) else "")
        existing_by_id = benefits.set_index("benefit_id", drop=False)
        for _, edited_row in edited.iterrows():
            benefit_id = clean_display(edited_row.get("benefit_id"), "")
            if not benefit_id or benefit_id not in existing_by_id.index:
                continue
            old_row = existing_by_id.loc[benefit_id]
            old_used = normalize_money(old_row.get("used_amount"))
            new_used = normalize_money(edited_row.get("used_amount"))
            usage_delta = new_used - old_used
            status = clean_display(edited_row.get("status"), "Not Used")
            if usage_delta > 0 and status in ["Used", "Partially Used"]:
                append_usage_record(
                    edited_row,
                    usage_delta,
                    status == "Used",
                    note="Logged from Edit Benefits save",
                )
        save_benefits(edited)
        st.success("Saved benefits.")
        st.rerun()


def show_add_forms(cards: pd.DataFrame, benefits: pd.DataFrame) -> None:
    title_block("Add New Data", "Add cards or benefits without editing raw CSV files.")
    left, right = st.columns(2)

    with left:
        st.subheader("Add Credit Card")
        with st.form("add_card"):
            owner = st.text_input("Owner / cardholder")
            card_name = st.text_input("Card name")
            issuer = st.text_input("Issuer")
            card_version = st.text_input("Card version")
            annual_fee = st.number_input("Annual fee", min_value=0.0, step=1.0)
            status = st.selectbox("Card status", ["Active", "Closed", "Considering"])
            notes = st.text_area("Notes")
            submitted = st.form_submit_button("Add card")
        if submitted and card_name:
            new_card = pd.DataFrame(
                [
                    {
                        "card_id": f"card_{uuid4().hex[:10]}",
                        "owner": owner,
                        "card_name": card_name,
                        "issuer": issuer,
                        "card_version": card_version,
                        "open_date": "",
                        "annual_fee": annual_fee,
                        "renewal_month": "",
                        "status": status,
                        "autopay": "",
                        "notes": notes,
                        "source_url": "",
                    }
                ],
                columns=CARD_COLUMNS,
            )
            save_cards(pd.concat([cards, new_card], ignore_index=True))
            st.success("Added card.")
            st.rerun()

    with right:
        st.subheader("Add Benefit")
        card_labels = {
            f"{row.owner} - {row.card_name}": row
            for row in cards.itertuples(index=False)
            if normalize_text(row.card_name)
        }
        with st.form("add_benefit"):
            selected = st.selectbox("Card", ["Manual / no card selected"] + list(card_labels.keys()))
            manual_owner = st.text_input("Owner", disabled=selected != "Manual / no card selected")
            manual_card = st.text_input("Card name", disabled=selected != "Manual / no card selected")
            benefit_name = st.text_input("Benefit name")
            category = st.text_input("Category")
            frequency = st.selectbox("Frequency", ["Monthly", "Quarterly", "Semiannual", "Annual", "One-time", "Custom"])
            cycle_rule = st.text_input("Cycle rule", value="Calendar Month" if frequency == "Monthly" else "")
            current_cycle = st.text_input("Current cycle", placeholder="2026-05, 2026-Q2, 2026-H1")
            face_value = st.number_input("Face value", min_value=0.0, step=1.0)
            realistic_value = st.number_input("Realistic value", min_value=0.0, step=1.0)
            used_amount = st.number_input("Used amount", min_value=0.0, step=1.0)
            expiration_date = st.date_input("Expiration date", value=None)
            status = st.selectbox("Status", STATUSES)
            priority = st.selectbox("Priority", ["High", "Medium", "Low", ""])
            include_in_alert = st.selectbox("Include in alert?", ["Yes", "No"])
            notes = st.text_area("Benefit notes")
            submitted = st.form_submit_button("Add benefit")

        if submitted and benefit_name:
            if selected == "Manual / no card selected":
                card_id = ""
                owner = manual_owner
                card_name = manual_card
            else:
                selected_card = card_labels[selected]
                card_id = selected_card.card_id
                owner = selected_card.owner
                card_name = selected_card.card_name

            remaining_amount = max(face_value - used_amount, 0)
            usage_percent = used_amount / face_value if face_value else 0
            new_benefit = pd.DataFrame(
                [
                    {
                        "benefit_id": f"benefit_{uuid4().hex[:10]}",
                        "card_id": card_id,
                        "owner": owner,
                        "card_name": card_name,
                        "benefit_name": benefit_name,
                        "benefit_type": "Credit",
                        "category": category,
                        "frequency": frequency,
                        "cycle_rule": cycle_rule,
                        "current_cycle": current_cycle,
                        "expiration_date": expiration_date.isoformat() if expiration_date else "",
                        "face_value": face_value,
                        "realistic_value": realistic_value,
                        "status": status,
                        "used_amount": used_amount,
                        "remaining_amount": remaining_amount,
                        "usage_percent": usage_percent,
                        "days_until_expiry": "",
                        "priority": priority,
                        "include_in_alert": include_in_alert,
                        "notes": notes,
                        "source_url": "",
                        "review_needed": "",
                    }
                ],
                columns=BENEFIT_COLUMNS,
            )
            save_benefits(pd.concat([benefits, new_benefit], ignore_index=True))
            st.success("Added benefit.")
            st.rerun()


def show_usage_log(usage: pd.DataFrame) -> None:
    title_block("Usage Log", "Imported usage records plus updates made from the dashboard and Edit Benefits.")
    if st.button("Sync from current benefit statuses"):
        added = sync_usage_log_from_benefits()
        if added:
            st.success(f"Added {added} missing usage record(s).")
        else:
            st.info("Usage log is already in sync.")
        st.rerun()

    editable = usage.copy()
    editable["used_date"] = pd.to_datetime(editable["used_date"], errors="coerce")
    edited = st.data_editor(
        editable,
        column_config={
            "usage_id": None,
            "used_date": st.column_config.DateColumn("used_date", format="YYYY-MM-DD"),
            "used_amount": st.column_config.NumberColumn("used_amount", min_value=0.0, step=1.0),
            "fully_used": st.column_config.SelectboxColumn("fully_used", options=["Yes", "No", ""]),
        },
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
    )
    if st.button("Save usage log", type="primary"):
        edited = edited.copy()
        edited["used_date"] = pd.to_datetime(edited["used_date"], errors="coerce").dt.date
        edited["used_date"] = edited["used_date"].apply(lambda value: value.isoformat() if pd.notna(value) else "")
        missing_ids = edited["usage_id"].isna() | (edited["usage_id"].astype(str).str.strip() == "")
        edited.loc[missing_ids, "usage_id"] = [f"usage_{uuid4().hex[:10]}" for _ in range(missing_ids.sum())]
        save_usage(edited)
        st.success("Saved usage log.")
        st.rerun()


def serialize_date_column(df: pd.DataFrame, column: str) -> None:
    if column not in df.columns:
        return
    dates = pd.to_datetime(df[column], errors="coerce").dt.date
    df[column] = dates.apply(lambda value: value.isoformat() if pd.notna(value) else "")


def fill_missing_ids(df: pd.DataFrame, column: str, prefix: str) -> None:
    if column not in df.columns:
        df[column] = ""
    missing = df[column].isna() | (df[column].astype(str).str.strip() == "")
    df.loc[missing, column] = [f"{prefix}_{uuid4().hex[:10]}" for _ in range(missing.sum())]


def show_raw_data(cards: pd.DataFrame, benefits: pd.DataFrame, usage: pd.DataFrame) -> None:
    title_block("Raw Data", "Edit the local CSV-backed tables directly.")
    st.caption("Changes are saved to the CSV files in the data folder. The original Excel file is not modified.")

    cards_tab, benefits_tab, usage_tab = st.tabs(["Cards", "Benefits", "Usage"])

    with cards_tab:
        editable_cards = cards.copy()
        editable_cards["open_date"] = pd.to_datetime(editable_cards["open_date"], errors="coerce")
        edited_cards = st.data_editor(
            editable_cards,
            column_config={
                "open_date": st.column_config.DateColumn("open_date", format="YYYY-MM-DD"),
                "annual_fee": st.column_config.NumberColumn("annual_fee", min_value=0.0, step=1.0),
                "status": st.column_config.SelectboxColumn("status", options=["Active", "Closed", "Considering", ""]),
            },
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            key="raw_cards_editor",
        )
        if st.button("Save cards CSV", type="primary"):
            edited_cards = edited_cards.copy()
            serialize_date_column(edited_cards, "open_date")
            fill_missing_ids(edited_cards, "card_id", "card")
            save_cards(edited_cards)
            st.success("Saved cards.csv.")
            st.rerun()

    with benefits_tab:
        editable_benefits = benefits.copy()
        editable_benefits["expiration_date"] = pd.to_datetime(editable_benefits["expiration_date"], errors="coerce")
        edited_benefits = st.data_editor(
            editable_benefits,
            column_config={
                "expiration_date": st.column_config.DateColumn("expiration_date", format="YYYY-MM-DD"),
                "face_value": st.column_config.NumberColumn("face_value", min_value=0.0, step=1.0),
                "realistic_value": st.column_config.NumberColumn("realistic_value", min_value=0.0, step=1.0),
                "used_amount": st.column_config.NumberColumn("used_amount", min_value=0.0, step=1.0),
                "remaining_amount": st.column_config.NumberColumn("remaining_amount", min_value=0.0, step=1.0),
                "usage_percent": st.column_config.NumberColumn("usage_percent", min_value=0.0, max_value=1.0, step=0.05),
                "days_until_expiry": st.column_config.NumberColumn("days_until_expiry", min_value=0.0, step=1.0),
                "status": st.column_config.SelectboxColumn("status", options=STATUSES),
                "priority": st.column_config.SelectboxColumn("priority", options=["High", "Medium", "Low", ""]),
                "include_in_alert": st.column_config.SelectboxColumn("include_in_alert", options=["Yes", "No", ""]),
            },
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            key="raw_benefits_editor",
        )
        if st.button("Save benefits CSV", type="primary"):
            edited_benefits = edited_benefits.copy()
            serialize_date_column(edited_benefits, "expiration_date")
            fill_missing_ids(edited_benefits, "benefit_id", "benefit")
            save_benefits(edited_benefits)
            st.success("Saved benefits.csv.")
            st.rerun()

    with usage_tab:
        editable_usage = usage.copy()
        editable_usage["used_date"] = pd.to_datetime(editable_usage["used_date"], errors="coerce")
        edited_usage = st.data_editor(
            editable_usage,
            column_config={
                "used_date": st.column_config.DateColumn("used_date", format="YYYY-MM-DD"),
                "used_amount": st.column_config.NumberColumn("used_amount", min_value=0.0, step=1.0),
                "fully_used": st.column_config.SelectboxColumn("fully_used", options=["Yes", "No", ""]),
            },
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            key="raw_usage_editor",
        )
        if st.button("Save usage CSV", type="primary"):
            edited_usage = edited_usage.copy()
            serialize_date_column(edited_usage, "used_date")
            fill_missing_ids(edited_usage, "usage_id", "usage")
            save_usage(edited_usage)
            st.success("Saved usage.csv.")
            st.rerun()


def main() -> None:
    st.set_page_config(page_title="Credit Card Benefit Tracker", layout="wide")
    ensure_data_files()
    inject_styles()

    st.markdown(
        """
        <div class="page-title-block">
            <h1>Credit Card Benefit Tracker</h1>
            <p>See which card benefits to use next, what is expiring soon, and how much value is still available.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cards = read_csv(CARDS_CSV, CARD_COLUMNS)
    benefits = read_csv(BENEFITS_CSV, BENEFIT_COLUMNS)
    usage = read_csv(USAGE_CSV, USAGE_COLUMNS)

    with st.sidebar:
        st.header("Data")
        st.write(f"Cards: {len(cards)}")
        st.write(f"Benefits: {len(benefits)}")
        st.write(f"Usage records: {len(usage)}")
        if ORIGINAL_EXCEL.exists():
            st.caption(f"Original Excel preserved: {ORIGINAL_EXCEL.name}")
        st.divider()
        section = st.radio(
            "Section",
            ["Dashboard", "UI Theme Preview", "Liquid Glass Preview", "Edit Benefits", "Usage Log", "Add", "Import Excel", "Raw Data"],
        )
        if st.button("Reload CSV files"):
            st.rerun()

    if benefits.empty:
        show_importer()
        st.divider()

    if section == "Dashboard":
        show_dashboard(benefits)
    elif section == "UI Theme Preview":
        show_theme_preview()
    elif section == "Liquid Glass Preview":
        show_liquid_glass_preview()
    elif section == "Edit Benefits":
        show_edit_benefits(benefits)
    elif section == "Usage Log":
        show_usage_log(usage)
    elif section == "Add":
        show_add_forms(cards, benefits)
    elif section == "Import Excel":
        show_importer()
    else:
        show_raw_data(cards, benefits, usage)


if __name__ == "__main__":
    main()

from __future__ import annotations

import base64
import json
from html import escape
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components

from alerts.rules import annual_fee_date, benefit_attention_window
from storage import BENEFIT_COLUMNS, CARD_COLUMNS, USAGE_COLUMNS, StorageBackend, get_storage


APP_DIR = Path(__file__).parent
ASSETS_DIR = APP_DIR / "assets"
APP_ICON_PATH = ASSETS_DIR / "app_icon.png"
APP_ICON_MIME_TYPE = "image/png"
APP_ICON_STATIC_URL = "/app/static/apple-touch-icon.png"
DATA_DIR = APP_DIR / "data"
ORIGINAL_EXCEL = DATA_DIR / "original_tracker.xlsx"
LIQUID_APP_CSS = APP_DIR / "styles" / "liquid_app.css"
WALLPAPER_DIR = APP_DIR / "wallpaper"
WALLPAPER_SETTINGS_JSON = WALLPAPER_DIR / "settings.json"
UI_SETTINGS_JSON = DATA_DIR / "ui_settings.json"
STORAGE: StorageBackend | None = None

STATUSES = ["Not Used", "Partially Used", "Used"]
EXPIRING_SOON_DAYS = 14
THEME_OPTIONS = {
    "Dark Wallet": "dark",
    "Light Ledger": "light",
}
THEME_LABELS = {value: label for label, value in THEME_OPTIONS.items()}

STATUS_COLORS = {
    "Used": ("rgba(209, 250, 229, .58)", "#047857"),
    "Partially Used": ("rgba(254, 243, 199, .62)", "#9a5c0a"),
    "Not Used": ("rgba(224, 242, 254, .62)", "#3157ad"),
    "Expiring Soon": ("rgba(254, 243, 199, .72)", "#b45309"),
}

CATEGORY_ICONS = {
    "airline": "✈️",
    "travel": "🧳",
    "hotel": "🏨",
    "dining": "🍽️",
    "rideshare": "🚗",
    "uber": "🚗",
    "grocery": "🛒",
    "entertainment": "🎟️",
    "shopping": "🛍️",
    "fitness": "💪",
    "wellness": "🧘",
    "other": "✨",
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
STATUS_COLORS["Ignored"] = ("rgba(226, 232, 240, .70)", "#64748b")
CATEGORY_ICONS = {
    "airline": "✈️",
    "travel": "🧳",
    "hotel": "🏨",
    "dining": "🍽️",
    "rideshare": "🚗",
    "uber": "🚗",
    "grocery": "🛒",
    "entertainment": "🎟️",
    "shopping": "🛍️",
    "fitness": "💪",
    "wellness": "🧘",
    "other": "✨",
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

def storage_backend() -> StorageBackend:
    global STORAGE
    if STORAGE is None:
        STORAGE = get_storage(DATA_DIR)
    return STORAGE


def ensure_data_files() -> None:
    storage_backend().ensure_data_files()


def app_icon_page_config_value() -> str | None:
    return str(APP_ICON_PATH) if APP_ICON_PATH.is_file() else None


def inject_app_icon_metadata() -> None:
    if not APP_ICON_PATH.is_file():
        return

    components.html(
        f"""
        <script>
        const iconHref = {json.dumps(APP_ICON_STATIC_URL)};
        const title = "Credit Card Benefit Tracker";
        const parentDoc = window.parent.document;

        function upsertLink(rel, href, sizes) {{
            const sizeSelector = sizes ? `[sizes="${{sizes}}"]` : "";
            let node = parentDoc.querySelector(`link[rel="${{rel}}"]${{sizeSelector}}`);
            if (!node) {{
                node = parentDoc.createElement("link");
                node.setAttribute("rel", rel);
                parentDoc.head.appendChild(node);
            }}
            node.setAttribute("href", href);
            node.setAttribute("type", {json.dumps(APP_ICON_MIME_TYPE)});
            if (sizes) {{
                node.setAttribute("sizes", sizes);
            }}
        }}

        function upsertMeta(name, content) {{
            let node = parentDoc.querySelector(`meta[name="${{name}}"]`);
            if (!node) {{
                node = parentDoc.createElement("meta");
                node.setAttribute("name", name);
                parentDoc.head.appendChild(node);
            }}
            node.setAttribute("content", content);
        }}

        upsertLink("icon", iconHref, "512x512");
        upsertLink("shortcut icon", iconHref, null);
        upsertLink("apple-touch-icon", iconHref, null);
        upsertLink("apple-touch-icon", iconHref, "512x512");
        upsertLink("apple-touch-icon-precomposed", iconHref, "512x512");

        upsertMeta("application-name", title);
        upsertMeta("apple-mobile-web-app-title", title);
        upsertMeta("apple-mobile-web-app-capable", "yes");
        upsertMeta("mobile-web-app-capable", "yes");
        upsertMeta("apple-mobile-web-app-status-bar-style", "default");
        upsertMeta("theme-color", "#f8fbff");
        </script>
        """,
        height=0,
        width=0,
    )


def read_cards() -> pd.DataFrame:
    return storage_backend().read_cards()


def read_benefits() -> pd.DataFrame:
    return storage_backend().read_benefits()


def read_usage() -> pd.DataFrame:
    return storage_backend().read_usage()


def save_cards(df: pd.DataFrame) -> None:
    storage_backend().save_cards(df)


def save_benefits(df: pd.DataFrame) -> None:
    storage_backend().save_benefits(df)


def save_usage(df: pd.DataFrame) -> None:
    storage_backend().save_usage(df)


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


def column_series(df: pd.DataFrame, column: str, default: object = "") -> pd.Series:
    if column in df.columns:
        return df[column]
    return pd.Series([default] * len(df), index=df.index)


def normalized_series(
    df: pd.DataFrame,
    column: str,
    normalizer=normalize_text,
    default: object = "",
) -> pd.Series:
    return column_series(df, column, default).map(normalizer)


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
            "card_id": normalized_series(cards_raw, "Card ID"),
            "owner": normalized_series(cards_raw, "Owner"),
            "card_name": normalized_series(cards_raw, "Card Name"),
            "issuer": normalized_series(cards_raw, "Issuer"),
            "card_version": normalized_series(cards_raw, "Assumed Card Version"),
            "open_date": normalized_series(cards_raw, "Open Date", normalize_date),
            "annual_fee": normalized_series(cards_raw, "Annual Fee", normalize_money),
            "renewal_month": normalized_series(cards_raw, "Renewal Month"),
            "status": normalized_series(cards_raw, "Status"),
            "autopay": normalized_series(cards_raw, "Autopay?", yes_no),
            "notes": normalized_series(cards_raw, "Notes"),
            "source_url": normalized_series(cards_raw, "Source URL"),
        }
    )
    cards = cards[cards["card_name"] != ""]

    master = pd.DataFrame(
        {
            "benefit_id": normalized_series(master_raw, "Benefit ID"),
            "card_id": normalized_series(master_raw, "Card ID"),
            "benefit_type": normalized_series(master_raw, "Benefit Type"),
            "category": normalized_series(master_raw, "Category"),
            "realistic_value": normalized_series(master_raw, "Realistic Value", normalize_money),
            "source_url": normalized_series(master_raw, "Source URL"),
            "review_needed": normalized_series(master_raw, "Review Needed?"),
        }
    )

    current = current_raw.merge(master, how="left", left_on="Benefit ID", right_on="benefit_id")
    benefits = pd.DataFrame(
        {
            "benefit_id": normalized_series(current, "Benefit ID"),
            "card_id": normalized_series(current, "card_id"),
            "owner": normalized_series(current, "Owner"),
            "card_name": normalized_series(current, "Card Name"),
            "benefit_name": normalized_series(current, "Benefit Name"),
            "benefit_type": normalized_series(current, "benefit_type"),
            "category": normalized_series(current, "category"),
            "frequency": normalized_series(current, "Frequency"),
            "cycle_rule": normalized_series(current, "Cycle Rule"),
            "current_cycle": normalized_series(current, "Current Cycle"),
            "expiration_date": normalized_series(current, "Expiry Date", normalize_date),
            "face_value": normalized_series(current, "Face Value", normalize_money),
            "realistic_value": normalized_series(current, "realistic_value", normalize_money),
            "used_amount": normalized_series(current, "Amount / Count Used", normalize_money),
            "remaining_amount": normalized_series(current, "Remaining", normalize_money),
            "usage_percent": normalized_series(current, "Usage %", normalize_money),
            "status": normalized_series(current, "Status"),
            "days_until_expiry": normalized_series(current, "Days Until Expiry", normalize_money),
            "priority": normalized_series(current, "Priority"),
            "include_in_alert": normalized_series(current, "Include in Alert?", yes_no),
            "notes": normalized_series(current, "Notes"),
            "source_url": normalized_series(current, "source_url"),
            "review_needed": normalized_series(current, "review_needed"),
        }
    )
    benefits = benefits[benefits["benefit_name"] != ""]

    usage = pd.DataFrame(
        {
            "usage_id": normalized_series(usage_raw, "Usage ID"),
            "used_date": normalized_series(usage_raw, "Date Used", normalize_date),
            "owner": normalized_series(usage_raw, "Owner"),
            "card_id": normalized_series(usage_raw, "Card ID"),
            "benefit_id": normalized_series(usage_raw, "Benefit ID"),
            "benefit_name": normalized_series(usage_raw, "Benefit Name"),
            "cycle_period": normalized_series(usage_raw, "Cycle Period"),
            "used_amount": normalized_series(usage_raw, "Amount / Count Used", normalize_money),
            "fully_used": normalized_series(usage_raw, "Fully Used?", yes_no),
            "merchant": normalized_series(usage_raw, "Merchant"),
            "notes": normalized_series(usage_raw, "Notes"),
        }
    )
    usage = usage[usage["benefit_name"] != ""]

    save_cards(cards)
    save_benefits(benefits)
    save_usage(usage)

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
    save_usage(read_usage())

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


def app_wallpaper_data_uri() -> str:
    preferred = WALLPAPER_DIR / "app_wallpaper.jpg"
    if preferred.exists():
        return card_image_data_uri(preferred)
    for extension in ["*.png", "*.jpg", "*.jpeg", "*.webp"]:
        matches = sorted(WALLPAPER_DIR.glob(extension))
        if matches:
            return card_image_data_uri(matches[0])
    return ""


DEFAULT_WALLPAPER_SETTINGS = {
    "overlay": 0.30,
    "blur": 3,
    "brightness": 1.04,
    "saturation": 1.05,
    "position": "center",
    "size": "cover",
}


def load_wallpaper_settings() -> dict[str, object]:
    if WALLPAPER_SETTINGS_JSON.exists():
        try:
            data = json.loads(WALLPAPER_SETTINGS_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    else:
        data = {}
    settings = DEFAULT_WALLPAPER_SETTINGS.copy()
    settings.update({key: data[key] for key in settings if key in data})
    return settings


def active_wallpaper_settings() -> dict[str, object]:
    return load_wallpaper_settings()


def load_ui_settings() -> dict[str, object]:
    if UI_SETTINGS_JSON.exists():
        try:
            data = json.loads(UI_SETTINGS_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}
    else:
        data = {}
    theme = str(data.get("theme", "dark")).lower()
    if theme not in THEME_LABELS:
        theme = "dark"
    hidden_ids = data.get("history_hidden_benefit_ids", [])
    if not isinstance(hidden_ids, list):
        hidden_ids = []
    hidden_ids = sorted({str(value) for value in hidden_ids if str(value).strip()})
    return {"theme": theme, "history_hidden_benefit_ids": hidden_ids}


def write_ui_settings(settings: dict[str, object]) -> None:
    theme = str(settings.get("theme", "dark")).lower()
    UI_SETTINGS_JSON.parent.mkdir(exist_ok=True)
    UI_SETTINGS_JSON.write_text(
        json.dumps(
            {
                "theme": theme if theme in THEME_LABELS else "dark",
                "history_hidden_benefit_ids": sorted(
                    {
                        str(value)
                        for value in settings.get("history_hidden_benefit_ids", [])
                        if str(value).strip()
                    }
                ),
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def save_ui_settings(theme: str) -> None:
    settings = load_ui_settings()
    settings["theme"] = theme if theme in THEME_LABELS else "dark"
    write_ui_settings(settings)


def history_hidden_benefit_ids() -> set[str]:
    return set(load_ui_settings().get("history_hidden_benefit_ids", []))


def save_history_hidden_benefit_ids(hidden_ids: set[str]) -> None:
    settings = load_ui_settings()
    settings["history_hidden_benefit_ids"] = sorted(hidden_ids)
    write_ui_settings(settings)


def hide_from_history(benefit_id: str) -> None:
    hidden_ids = history_hidden_benefit_ids()
    hidden_ids.add(benefit_id)
    save_history_hidden_benefit_ids(hidden_ids)
    st.toast("Hidden from History")
    st.rerun()


def restore_to_history(benefit_id: str) -> None:
    hidden_ids = history_hidden_benefit_ids()
    hidden_ids.discard(benefit_id)
    save_history_hidden_benefit_ids(hidden_ids)
    st.toast("Restored to History")
    st.rerun()


def active_app_theme() -> str:
    if "app_theme" not in st.session_state:
        st.session_state["app_theme"] = load_ui_settings()["theme"]
    theme = str(st.session_state["app_theme"])
    return theme if theme in THEME_LABELS else "dark"


def wallpaper_settings_css(settings: dict[str, object]) -> str:
    overlay = float(settings["overlay"])
    blur = int(settings["blur"])
    brightness = float(settings["brightness"])
    saturation = float(settings["saturation"])
    position = escape(str(settings["position"]))
    size = escape(str(settings["size"]))
    return f"""
    <style>
    :root {{
        --wallpaper-overlay: {overlay};
        --wallpaper-blur: {blur}px;
        --wallpaper-brightness: {brightness};
        --wallpaper-saturation: {saturation};
        --wallpaper-position: {position};
        --wallpaper-size: {size};
    }}
    </style>
    """


def inject_styles() -> None:
    if LIQUID_APP_CSS.exists():
        css = LIQUID_APP_CSS.read_text(encoding="utf-8")
        wallpaper_uri = app_wallpaper_data_uri()
        if wallpaper_uri:
            css = css.replace(
                'url("../wallpaper/app_wallpaper.jpg")',
                f'url("{wallpaper_uri}")',
            )
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        st.markdown(wallpaper_settings_css(active_wallpaper_settings()), unsafe_allow_html=True)


def theme_override_css(theme: str) -> str:
    if theme == "light":
        return """
        <style>
        :root {
            --theme-bg-0: #f6f8fc;
            --theme-bg-1: #eef3f8;
            --theme-surface: rgba(255, 255, 255, .88);
            --theme-surface-strong: rgba(255, 255, 255, .96);
            --theme-surface-soft: rgba(248, 250, 252, .92);
            --theme-border: rgba(148, 163, 184, .32);
            --theme-border-strong: rgba(71, 85, 105, .26);
            --theme-text: #172033;
            --theme-muted: #526173;
            --theme-soft: #728095;
            --theme-accent: #2457c5;
            --theme-accent-2: #0f766e;
            --theme-warning: #a16207;
            --theme-danger: #be123c;
            --theme-shadow: 0 1px 2px rgba(15, 23, 42, .05), 0 14px 30px rgba(15, 23, 42, .08);
            --wallet-text: var(--theme-text);
            --wallet-muted: var(--theme-muted);
            --wallet-soft: var(--theme-soft);
            --wallet-accent: var(--theme-accent);
            --wallet-accent-2: var(--theme-accent);
        }

        html,
        body,
        body .stApp {
            color-scheme: light;
            background-color: var(--theme-bg-0) !important;
        }

        body .stApp {
            color: var(--theme-text) !important;
            background:
                linear-gradient(180deg, rgba(255,255,255,.82), rgba(246,248,252,.92)),
                var(--app-wallpaper),
                linear-gradient(145deg, var(--theme-bg-0), var(--theme-bg-1)) !important;
            background-size: var(--wallpaper-size, cover);
            background-position: var(--wallpaper-position, center);
            background-repeat: no-repeat;
            background-attachment: fixed;
        }

        body .stApp:before {
            background:
                linear-gradient(180deg, rgba(255,255,255,.62), rgba(246,248,252,.82)),
                linear-gradient(90deg, rgba(148,163,184,.055) 1px, transparent 1px),
                linear-gradient(180deg, rgba(148,163,184,.04) 1px, transparent 1px) !important;
            background-size: auto, 96px 96px, 96px 96px !important;
            backdrop-filter: blur(var(--wallpaper-blur, 2px)) saturate(1.02) brightness(1.04) !important;
            -webkit-backdrop-filter: blur(var(--wallpaper-blur, 2px)) saturate(1.02) brightness(1.04) !important;
        }

        body .stApp,
        body .stApp p,
        body .stApp span,
        body .stApp label,
        body .stApp div,
        body .stApp li,
        body .stApp td,
        body .stApp th,
        body .stApp small,
        body .stApp [data-testid="stMarkdownContainer"],
        body .stApp [data-testid="stMarkdownContainer"] * {
            color: var(--theme-text) !important;
        }

        body .stApp .page-title-block,
        body .stApp .section-title-block,
        body .stApp .glass-panel,
        body .stApp .glass-card,
        body .stApp .glass-content-panel,
        body .stApp .glass-metric-card,
        body .stApp .metric-card,
        body .stApp .filter-bar,
        body .stApp .form-section,
        body .stApp .st-key-dashboard_controls,
        body .stApp [data-testid="stVerticalBlockBorderWrapper"],
        body .stApp [data-testid="stExpander"],
        body .stApp [data-testid="stForm"],
        body .stApp [data-testid="stAlert"],
        body .stApp [data-testid="stDataFrame"],
        body .stApp [data-testid="stDataEditor"] {
            color: var(--theme-text) !important;
            border: 1px solid var(--theme-border) !important;
            background: var(--theme-surface) !important;
            box-shadow: var(--theme-shadow) !important;
            backdrop-filter: blur(16px) saturate(1.04) !important;
            -webkit-backdrop-filter: blur(16px) saturate(1.04) !important;
        }

        body .stApp .page-title-block {
            background:
                linear-gradient(90deg, rgba(36,87,197,.10), rgba(15,118,110,.055)),
                var(--theme-surface-strong) !important;
            border-radius: 22px !important;
        }

        body .stApp .mobile-wallet-hero {
            color: var(--theme-text) !important;
            border: 1px solid var(--theme-border) !important;
            background:
                radial-gradient(circle at 86% 0%, rgba(36,87,197,.16), transparent 42%),
                radial-gradient(circle at 8% 16%, rgba(15,118,110,.12), transparent 44%),
                linear-gradient(145deg, rgba(255,255,255,.96), rgba(248,250,252,.84)) !important;
            box-shadow: var(--theme-shadow) !important;
        }

        body .stApp .mobile-wallet-hero:before {
            background:
                linear-gradient(115deg, rgba(255,255,255,.42), transparent 42%),
                radial-gradient(circle at 88% 0%, rgba(36,87,197,.10), transparent 44%) !important;
            opacity: .88 !important;
        }

        body .stApp .mobile-wallet-topline span,
        body .stApp .mobile-wallet-balance-label,
        body .stApp .mobile-wallet-stats span,
        body .stApp .mobile-wallet-chip-row span {
            color: var(--theme-muted) !important;
        }

        body .stApp .mobile-wallet-balance,
        body .stApp .mobile-wallet-stats strong {
            color: var(--theme-text) !important;
            text-shadow: none !important;
        }

        body .stApp .mobile-wallet-chip-row span {
            border-color: rgba(36,87,197,.18) !important;
            background: rgba(219,234,254,.88) !important;
        }

        body .stApp .mobile-wallet-stats > div,
        body .stApp .dashboard-kpi-card,
        body .stApp div[data-testid="stMetric"],
        body .stApp .card-stat-grid > div,
        body .stApp .mini-stat,
        body .stApp .mobile-checklist-summary > div,
        body .stApp .mobile-benefit-facts > div {
            color: var(--theme-text) !important;
            border: 1px solid var(--theme-border) !important;
            background: var(--theme-surface-strong) !important;
            box-shadow: 0 1px 2px rgba(15,23,42,.04) !important;
        }

        body .stApp .benefit-row,
        body .stApp .benefit-tile,
        body .stApp .mobile-benefit-card,
        body .stApp .history-card {
            color: var(--theme-text) !important;
            border: 1px solid var(--theme-border) !important;
            background: var(--theme-surface-strong) !important;
            box-shadow: 0 1px 2px rgba(15,23,42,.04), 0 10px 24px rgba(15,23,42,.07) !important;
        }

        body .stApp .history-summary-strip {
            display: grid !important;
            grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
            gap: 10px !important;
            margin: 10px 0 12px !important;
        }

        body .stApp .history-summary-strip > div {
            color: var(--theme-text) !important;
            border: 1px solid var(--theme-border) !important;
            background: var(--theme-surface-strong) !important;
            border-radius: 16px !important;
            padding: 11px 12px !important;
            box-shadow: 0 1px 2px rgba(15,23,42,.04) !important;
        }

        body .stApp .history-summary-strip span,
        body .stApp .history-benefit-meta,
        body .stApp .history-row-footer,
        body .stApp .history-legend {
            color: var(--theme-muted) !important;
        }

        body .stApp .history-summary-strip span,
        body .stApp .history-summary-strip strong {
            display: block !important;
        }

        body .stApp .history-summary-strip strong {
            margin-top: 3px !important;
            font-size: 1.18rem !important;
            line-height: 1 !important;
        }

        body .stApp .history-summary-strip strong,
        body .stApp .history-benefit-name {
            color: var(--theme-text) !important;
        }

        body .stApp .history-owner-heading {
            display: flex !important;
            align-items: baseline !important;
            justify-content: space-between !important;
            gap: 10px !important;
            margin: 18px 0 8px !important;
            padding: 0 2px !important;
        }

        body .stApp .history-owner-heading span {
            color: var(--theme-text) !important;
            font-size: 1.05rem !important;
            font-weight: 900 !important;
            letter-spacing: 0 !important;
        }

        body .stApp .history-owner-heading small {
            color: var(--theme-muted) !important;
            font-size: .76rem !important;
            font-weight: 750 !important;
        }

        body .stApp .history-card {
            margin: 10px 0 13px !important;
            padding: 14px !important;
            border-radius: 20px !important;
            position: relative !important;
        }

        body .stApp .history-card-hidden {
            opacity: .48 !important;
            filter: grayscale(.82) saturate(.38) !important;
            border-style: dashed !important;
            background:
                linear-gradient(145deg, rgba(241,245,249,.82), rgba(226,232,240,.58)) !important;
            box-shadow: none !important;
        }

        body .stApp .history-card-hidden:after {
            content: "Hidden" !important;
            position: absolute !important;
            top: 12px !important;
            right: 14px !important;
            color: var(--theme-muted) !important;
            border: 1px solid var(--theme-border) !important;
            background: rgba(248,250,252,.86) !important;
            border-radius: 999px !important;
            padding: 4px 8px !important;
            font-size: .68rem !important;
            font-weight: 850 !important;
        }

        body .stApp .history-card-hidden .history-rate-pill {
            visibility: hidden !important;
        }

        body .stApp .history-card-hidden .history-cell-used,
        body .stApp .history-card-hidden .history-cell-partial,
        body .stApp .history-card-hidden .history-cell-missed,
        body .stApp .history-card-hidden .history-cell-open,
        body .stApp .history-card-hidden .history-cell-future,
        body .stApp .history-card-hidden .history-cell-untracked {
            color: rgba(71,85,105,.86) !important;
            background: rgba(203,213,225,.42) !important;
            border-color: rgba(148,163,184,.22) !important;
        }

        body .stApp .history-hidden-pill {
            color: var(--theme-muted) !important;
            border: 1px solid var(--theme-border) !important;
            background: rgba(248,250,252,.74) !important;
            border-radius: 999px !important;
            margin-top: 6px !important;
            padding: 4px 8px !important;
            font-size: .68rem !important;
            font-weight: 800 !important;
            text-align: center !important;
        }

        body .stApp [class*="st-key-history_actions_"] {
            margin: -7px 0 10px !important;
        }

        body .stApp button[data-testid="stBaseButton-pills"],
        body .stApp button[kind="pills"] {
            color: var(--theme-muted) !important;
            -webkit-text-fill-color: var(--theme-muted) !important;
            border: 1px solid var(--theme-border) !important;
            background: rgba(248,250,252,.88) !important;
            box-shadow: 0 1px 2px rgba(15,23,42,.04) !important;
        }

        body .stApp button[data-testid="stBaseButton-pills"] *,
        body .stApp button[kind="pills"] * {
            color: var(--theme-muted) !important;
            -webkit-text-fill-color: var(--theme-muted) !important;
        }

        body .stApp button[data-testid="stBaseButton-pillsActive"],
        body .stApp button[kind="pillsActive"] {
            color: var(--theme-accent) !important;
            -webkit-text-fill-color: var(--theme-accent) !important;
            border: 1px solid rgba(36,87,197,.24) !important;
            background: rgba(219,234,254,.92) !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.72), 0 3px 10px rgba(36,87,197,.10) !important;
        }

        body .stApp button[data-testid="stBaseButton-pillsActive"] *,
        body .stApp button[kind="pillsActive"] * {
            color: var(--theme-accent) !important;
            -webkit-text-fill-color: var(--theme-accent) !important;
        }

        body .stApp .history-card-top,
        body .stApp .history-title-row,
        body .stApp .history-row-footer,
        body .stApp .history-legend {
            display: flex !important;
            align-items: center !important;
        }

        body .stApp .history-card-top {
            justify-content: space-between !important;
            gap: 10px !important;
            margin-bottom: 12px !important;
        }

        body .stApp .history-title-row {
            gap: 10px !important;
            min-width: 0 !important;
        }

        body .stApp .history-title-row > div {
            min-width: 0 !important;
        }

        body .stApp .history-icon {
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            flex: 0 0 auto !important;
            width: 32px !important;
            height: 32px !important;
            border-radius: 12px !important;
            border: 1px solid rgba(36,87,197,.14) !important;
            background: linear-gradient(145deg, rgba(255,255,255,.96), rgba(226,232,240,.74)) !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.78), 0 5px 14px rgba(15,23,42,.08) !important;
        }

        body .stApp .history-rate-pill {
            flex: 0 0 auto !important;
            color: var(--theme-accent) !important;
            border: 1px solid rgba(36,87,197,.18) !important;
            background: rgba(219,234,254,.78) !important;
            border-radius: 999px !important;
            padding: 6px 9px !important;
            font-size: .76rem !important;
            font-weight: 800 !important;
        }

        body .stApp .history-benefit-name {
            font-size: .98rem !important;
            font-weight: 850 !important;
            line-height: 1.18 !important;
        }

        body .stApp .history-benefit-meta {
            margin-top: 3px !important;
            font-size: .80rem !important;
            font-weight: 650 !important;
            line-height: 1.25 !important;
        }

        body .stApp .history-month-labels,
        body .stApp .history-grid {
            display: grid !important;
            grid-template-columns: repeat(12, minmax(20px, 1fr)) !important;
            gap: 5px !important;
        }

        body .stApp .history-month-labels {
            margin: 2px 0 5px !important;
        }

        body .stApp .history-month-labels span {
            color: var(--theme-soft) !important;
            text-align: center !important;
            font-size: .64rem !important;
            font-weight: 800 !important;
        }

        body .stApp .history-cell {
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            aspect-ratio: 1 / 1 !important;
            min-height: 20px !important;
            border-radius: 7px !important;
            font-size: .68rem !important;
            font-weight: 900 !important;
            line-height: 1 !important;
            border: 1px solid transparent !important;
        }

        body .stApp .history-cell-used,
        body .stApp .history-dot-used {
            color: #064e3b !important;
            background: linear-gradient(180deg, #86efac, #34d399) !important;
            border-color: rgba(4,120,87,.16) !important;
        }

        body .stApp .history-cell-partial,
        body .stApp .history-dot-partial {
            color: #713f12 !important;
            background: linear-gradient(180deg, #fde68a, #fbbf24) !important;
            border-color: rgba(161,98,7,.18) !important;
        }

        body .stApp .history-cell-missed,
        body .stApp .history-dot-missed {
            color: #7f1d1d !important;
            background: linear-gradient(180deg, #fecaca, #f87171) !important;
            border-color: rgba(185,28,28,.18) !important;
        }

        body .stApp .history-cell-open,
        body .stApp .history-dot-open {
            background: rgba(219,234,254,.64) !important;
            border-color: rgba(36,87,197,.16) !important;
        }

        body .stApp .history-cell-future {
            background: rgba(226,232,240,.56) !important;
            border-color: rgba(148,163,184,.22) !important;
        }

        body .stApp .history-cell-untracked {
            background: rgba(226,232,240,.22) !important;
            border-color: rgba(148,163,184,.10) !important;
        }

        body .stApp .history-row-footer,
        body .stApp .history-legend {
            gap: 10px !important;
            flex-wrap: wrap !important;
            margin-top: 10px !important;
            font-size: .74rem !important;
            font-weight: 750 !important;
        }

        body .stApp .history-dot {
            display: inline-flex !important;
            width: 10px !important;
            height: 10px !important;
            border-radius: 3px !important;
            margin-right: 5px !important;
            vertical-align: -1px !important;
        }

        @media (max-width: 640px) {
            body .stApp .history-summary-strip {
                grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
            }

            body .stApp .history-card {
                padding: 13px !important;
            }

            body .stApp .history-card-top {
                align-items: flex-start !important;
            }

            body .stApp .history-rate-pill {
                font-size: .68rem !important;
                padding: 5px 7px !important;
            }

            body .stApp .history-month-labels,
            body .stApp .history-grid {
                gap: 4px !important;
            }
        }

        body .stApp .benefit-title-row,
        body .stApp .mobile-benefit-title-row {
            display: flex !important;
            align-items: flex-start !important;
            gap: 10px !important;
            min-width: 0 !important;
        }

        body .stApp .benefit-title-row > div,
        body .stApp .mobile-benefit-title-row > div {
            min-width: 0 !important;
        }

        body .stApp .benefit-visual-cue,
        body .stApp .mobile-benefit-visual,
        body .stApp .mobile-section-emoji {
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            flex: 0 0 auto !important;
            width: 30px !important;
            height: 30px !important;
            border-radius: 12px !important;
            border: 1px solid rgba(36,87,197,.14) !important;
            background:
                linear-gradient(145deg, rgba(255,255,255,.96), rgba(226,232,240,.74)) !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.78), 0 5px 14px rgba(15,23,42,.08) !important;
            font-size: 1rem !important;
            line-height: 1 !important;
            -webkit-text-fill-color: currentColor !important;
        }

        body .stApp .mobile-section-heading {
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
        }

        body .stApp .mobile-section-heading:before {
            content: none !important;
            display: none !important;
        }

        body .stApp .mobile-section-emoji {
            width: 24px !important;
            height: 24px !important;
            border-radius: 9px !important;
            font-size: .86rem !important;
        }

        body .stApp [data-testid="stExpander"] summary,
        body .stApp [data-testid="stExpander"] summary *,
        body .stApp [data-testid="stExpander"] [data-testid="stMarkdownContainer"],
        body .stApp [data-testid="stExpander"] [data-testid="stMarkdownContainer"] * {
            color: var(--theme-text) !important;
        }

        body .stApp [data-testid="stExpander"] summary {
            background:
                linear-gradient(180deg, rgba(255,255,255,.92), rgba(248,250,252,.72)) !important;
            border-bottom: 1px solid rgba(148,163,184,.22) !important;
        }

        body .stApp [data-testid="stExpander"] details,
        body .stApp [data-testid="stExpander"] details > div,
        body .stApp [data-testid="stExpander"] div[role="region"] {
            background: rgba(248,250,252,.58) !important;
        }

        body .stApp [data-testid="stExpander"] summary [class*="stMarkdownColoredText"],
        body .stApp [data-testid="stExpander"] summary [class*="stMarkdownColoredText"] *,
        body .stApp [data-testid="stCaptionContainer"],
        body .stApp [data-testid="stCaptionContainer"] *,
        body .stApp .benefit-secondary,
        body .stApp .mobile-benefit-card-name,
        body .stApp .mobile-benefit-owner,
        body .stApp .mobile-card-group-owner,
        body .stApp .mobile-card-group-stats,
        body .stApp .dashboard-kpi-card span,
        body .stApp .card-stat-grid span,
        body .stApp .mini-label,
        body .stApp .mobile-benefit-facts span,
        body .stApp .mobile-benefit-facts small,
        body .stApp .card-section-owner,
        body .stApp [data-testid="stWidgetLabel"] p {
            color: var(--theme-muted) !important;
        }

        body .stApp .benefit-title,
        body .stApp .mobile-benefit-name,
        body .stApp .mobile-card-group-title,
        body .stApp .card-section-header h3,
        body .stApp .dashboard-kpi-card strong,
        body .stApp div[data-testid="stMetric"] [data-testid="stMetricValue"],
        body .stApp .card-stat-grid strong,
        body .stApp .mini-value,
        body .stApp .mobile-benefit-facts strong,
        body .stApp .mobile-card-group-stats strong {
            color: var(--theme-text) !important;
            text-shadow: none !important;
        }

        body .stApp .mobile-card-group-header {
            color: var(--theme-text) !important;
            border: 1px solid var(--theme-border) !important;
            background:
                linear-gradient(145deg, rgba(255,255,255,.96), rgba(248,250,252,.86)) !important;
            box-shadow: 0 1px 2px rgba(15,23,42,.04), 0 10px 22px rgba(15,23,42,.07) !important;
        }

        body .stApp .mobile-card-group-header,
        body .stApp .mobile-card-group-header * {
            background-color: transparent !important;
        }

        body .stApp .mobile-card-group-image,
        body .stApp .mobile-card-group-fallback,
        body .stApp .card-cue,
        body .stApp .card-cue-fallback {
            border-color: rgba(15,23,42,.12) !important;
            background: #eef2f7 !important;
            box-shadow: 0 5px 14px rgba(15,23,42,.12) !important;
        }

        body .stApp .status-pill,
        body .stApp .badge,
        body .stApp .glass-chip,
        body .stApp .chip,
        body .stApp .chip-muted,
        body .stApp .card-section-status,
        body .stApp .deadline,
        body .stApp .mobile-status {
            color: var(--theme-muted) !important;
            border-color: var(--theme-border) !important;
            background: rgba(248,250,252,.92) !important;
            box-shadow: none !important;
        }

        body .stApp .deadline.soon,
        body .stApp .mobile-status-expiring-soon {
            color: var(--theme-danger) !important;
            background: #ffe4e6 !important;
            border-color: rgba(190,18,60,.16) !important;
        }

        body .stApp .deadline.done,
        body .stApp .mobile-status-used {
            color: var(--theme-accent-2) !important;
            background: #ccfbf1 !important;
            border-color: rgba(15,118,110,.18) !important;
        }

        body .stApp .mobile-status-available,
        body .stApp .mobile-status-partially-used {
            color: var(--theme-accent) !important;
            background: #dbeafe !important;
            border-color: rgba(36,87,197,.18) !important;
        }

        body .stApp .st-key-dashboard_controls,
        body .stApp div[data-testid="stTabs"] [role="tablist"],
        body .stApp .st-key-mobile_dashboard div[data-testid="stRadio"] [role="radiogroup"],
        body .stApp .st-key-mobile_theme_switch [role="radiogroup"],
        body .stApp .st-key-desktop_theme_switch [role="radiogroup"] {
            border-color: var(--theme-border) !important;
            background: rgba(226,232,240,.62) !important;
            box-shadow: inset 0 1px 2px rgba(15,23,42,.04) !important;
        }

        body .stApp div[data-testid="stRadio"] [data-baseweb="radio"],
        body .stApp div[data-testid="stTabs"] button,
        body .stApp .st-key-mobile_theme_switch [data-baseweb="radio"],
        body .stApp .st-key-desktop_theme_switch [data-baseweb="radio"] {
            color: var(--theme-muted) !important;
            background: transparent !important;
        }

        body .stApp div[data-testid="stRadio"] [data-baseweb="radio"]:has(input:checked),
        body .stApp div[data-testid="stTabs"] button[aria-selected="true"],
        body .stApp .st-key-mobile_dashboard div[data-testid="stRadio"] [data-baseweb="radio"]:has(input:checked),
        body .stApp .st-key-mobile_theme_switch [data-baseweb="radio"]:has(input:checked),
        body .stApp .st-key-desktop_theme_switch [data-baseweb="radio"]:has(input:checked) {
            color: var(--theme-accent) !important;
            border-color: rgba(36,87,197,.18) !important;
            background: var(--theme-surface-strong) !important;
            box-shadow: 0 1px 2px rgba(15,23,42,.04), 0 6px 14px rgba(36,87,197,.10) !important;
        }

        body .stApp .st-key-mobile_theme_switch [data-testid="stWidgetLabel"] p,
        body .stApp .st-key-desktop_theme_switch [data-testid="stWidgetLabel"] p {
            color: var(--theme-muted) !important;
        }

        body .stApp div[data-testid="stButton"] button,
        body .stApp div[data-testid="stFormSubmitButton"] button,
        body .stApp div[data-testid="stLinkButton"] a,
        body .stApp div[data-testid="stDownloadButton"] button {
            color: var(--theme-text) !important;
            border-color: var(--theme-border) !important;
            background: var(--theme-surface-strong) !important;
            box-shadow: 0 1px 2px rgba(15,23,42,.04) !important;
        }

        body .stApp div[data-testid="stButton"] button[kind="primary"],
        body .stApp div[data-testid="stFormSubmitButton"] button[kind="primary"] {
            color: #ffffff !important;
            border-color: rgba(36,87,197,.24) !important;
            background: linear-gradient(180deg, #2f63dc, #2457c5) !important;
            box-shadow: 0 10px 22px rgba(36,87,197,.22) !important;
        }

        body .stApp div[data-baseweb="select"] > div,
        body .stApp div[data-baseweb="input"] > div,
        body .stApp div[data-baseweb="textarea"] > div,
        body .stApp div[data-baseweb="popover"],
        body .stApp div[data-baseweb="popover"] > div,
        body .stApp ul[role="listbox"] {
            color: var(--theme-text) !important;
            border-color: var(--theme-border) !important;
            background: var(--theme-surface-strong) !important;
        }

        body .stApp input,
        body .stApp textarea,
        body .stApp select,
        body .stApp [role="option"],
        body .stApp [role="option"] *,
        body .stApp [role="listbox"],
        body .stApp [role="listbox"] * {
            color: var(--theme-text) !important;
        }

        body .stApp input::placeholder,
        body .stApp textarea::placeholder {
            color: rgba(82,97,115,.62) !important;
        }

        body .stApp a,
        body .stApp [data-testid="stMarkdownContainer"] a {
            color: var(--theme-accent) !important;
        }

        body .stApp .st-key-mobile_dashboard [data-testid="stMarkdownContainer"]:has(.mobile-section-heading),
        body .stApp [class*="st-key-mobile_dashboard"] [data-testid="stMarkdownContainer"]:has(.mobile-section-heading) {
            margin: 18px 0 10px !important;
        }

        body .stApp .st-key-mobile_dashboard div[data-testid="stExpander"] {
            margin: 0 0 13px !important;
            border-radius: 18px !important;
        }

        body .stApp .st-key-mobile_dashboard div[data-testid="stExpander"] summary {
            min-height: 54px !important;
            padding: 12px 14px !important;
        }

        body .stApp .st-key-mobile_dashboard div[data-testid="stExpander"] details > div {
            padding: 12px 12px 16px !important;
        }

        body .stApp .mobile-card-group-header {
            margin: 8px 0 14px !important;
            padding: 10px 12px !important;
            border-radius: 18px !important;
        }

        body .stApp .mobile-benefit-card {
            margin: 8px 0 12px !important;
            padding: 14px !important;
            border-radius: 20px !important;
        }

        body .stApp .mobile-benefit-facts {
            gap: 8px !important;
            margin-top: 12px !important;
        }

        body .stApp .mobile-benefit-facts > div {
            min-height: 72px !important;
            padding: 10px 11px !important;
            border-radius: 16px !important;
        }

        body .stApp .mobile-detail-note {
            color: var(--theme-text) !important;
            border: 1px solid var(--theme-border) !important;
            background: var(--theme-surface-strong) !important;
            border-radius: 18px !important;
            margin: 12px 0 6px !important;
            padding: 13px 14px !important;
            box-shadow: 0 1px 2px rgba(15,23,42,.04), 0 10px 22px rgba(15,23,42,.06) !important;
        }

        body .stApp .mobile-detail-note span {
            color: var(--theme-text) !important;
        }

        body .stApp .mobile-detail-note p {
            color: var(--theme-muted) !important;
        }

        body .stApp .mobile-adjust-summary {
            color: var(--theme-muted) !important;
            border: 1px solid var(--theme-border) !important;
            background: var(--theme-surface-strong) !important;
            border-radius: 16px !important;
            margin: 12px 0 10px !important;
            padding: 11px 13px !important;
            box-shadow: 0 1px 2px rgba(15,23,42,.04) !important;
        }

        body .stApp .mobile-empty-state {
            color: var(--theme-muted) !important;
            border: 1px solid var(--theme-border) !important;
            background: var(--theme-surface-soft) !important;
            border-radius: 16px !important;
            padding: 10px 12px !important;
            margin: 8px 0 12px !important;
            box-shadow: none !important;
        }

        body .stApp .st-key-mobile_dashboard div[data-testid="stExpander"] [data-testid="stVerticalBlock"] {
            gap: 8px !important;
            row-gap: 8px !important;
        }

        body .stApp .st-key-mobile_dashboard div[data-testid="stExpander"] [data-testid="stMarkdownContainer"]:has(.mobile-section-heading),
        body .stApp .st-key-mobile_dashboard div[data-testid="stExpander"] .mobile-section-heading {
            margin-top: 4px !important;
            margin-bottom: 2px !important;
        }

        body .stApp [data-testid="stSlider"] [data-baseweb="slider"] > div {
            background:
                linear-gradient(180deg, rgba(203, 213, 225, .82), rgba(148, 163, 184, .58)) !important;
            border-radius: 999px !important;
            box-shadow: inset 0 1px 2px rgba(15, 23, 42, .08) !important;
        }

        body .stApp [data-testid="stSlider"] [data-baseweb="slider"] > div > div {
            background-color: transparent !important;
        }

        body .stApp [data-testid="stSlider"] [data-baseweb="slider"] > div > div > div > div:last-child,
        body .stApp [data-testid="stSlider"] [data-baseweb="slider"] div[class*="st-c7"] {
            opacity: 1 !important;
            filter: none !important;
            border-radius: 999px !important;
            box-shadow: inset 0 1px 0 rgba(255,255,255,.18) !important;
        }

        body .stApp [data-testid="stSlider"] [data-baseweb="slider"] [aria-valuenow] {
            position: relative !important;
            z-index: 3 !important;
            background: #4f7fe8 !important;
            border-color: #ffffff !important;
            box-shadow: 0 0 0 4px rgba(79,127,232,.14), 0 5px 12px rgba(15,23,42,.16) !important;
        }

        body .stApp [data-testid="stSlider"] [data-testid="stSliderTickBar"],
        body .stApp [data-testid="stSlider"] [data-testid="stSliderTickBar"] [data-testid="stMarkdownContainer"] {
            background: transparent !important;
        }
        </style>
        """

    return """
    <style>
    html,
    body,
    body .stApp {
        color-scheme: dark;
    }

    body .stApp .st-key-mobile_dashboard [data-testid="stMarkdownContainer"]:has(.mobile-section-heading),
    body .stApp [class*="st-key-mobile_dashboard"] [data-testid="stMarkdownContainer"]:has(.mobile-section-heading) {
        margin: 18px 0 10px !important;
    }

    body .stApp .st-key-mobile_dashboard div[data-testid="stExpander"] {
        margin: 0 0 13px !important;
        border-radius: 18px !important;
    }

    body .stApp .st-key-mobile_dashboard div[data-testid="stExpander"] summary {
        min-height: 54px !important;
        padding: 12px 14px !important;
        color: #f7f3fb !important;
        -webkit-text-fill-color: #f7f3fb !important;
    }

    body .stApp .st-key-mobile_dashboard div[data-testid="stExpander"] summary p,
    body .stApp .st-key-mobile_dashboard div[data-testid="stExpander"] summary div,
    body .stApp .st-key-mobile_dashboard div[data-testid="stExpander"] summary span,
    body .stApp .st-key-mobile_dashboard div[data-testid="stExpander"] summary strong,
    body .stApp .st-key-mobile_dashboard div[data-testid="stExpander"] summary b,
    body .stApp .st-key-mobile_dashboard div[data-testid="stExpander"] summary [data-testid="stMarkdownContainer"],
    body .stApp .st-key-mobile_dashboard div[data-testid="stExpander"] summary [data-testid="stMarkdownContainer"] * {
        color: #f7f3fb !important;
        -webkit-text-fill-color: #f7f3fb !important;
    }

    body .stApp .st-key-mobile_dashboard div[data-testid="stExpander"] summary [class*="stMarkdownColoredText"],
    body .stApp .st-key-mobile_dashboard div[data-testid="stExpander"] summary [class*="stMarkdownColoredText"] *,
    body .stApp .st-key-mobile_dashboard div[data-testid="stExpander"] summary p span:not(:first-child) {
        color: #d7d0df !important;
        -webkit-text-fill-color: #d7d0df !important;
    }

    body .stApp .st-key-mobile_dashboard div[data-testid="stExpander"] summary [class*="material"],
    body .stApp .st-key-mobile_dashboard div[data-testid="stExpander"] summary [data-testid*="Icon"] {
        color: #b8d1ff !important;
        -webkit-text-fill-color: #b8d1ff !important;
    }

    body .stApp .st-key-mobile_dashboard div[data-testid="stExpander"] details > div {
        padding: 12px 12px 16px !important;
        background:
            radial-gradient(circle at 92% 6%, rgba(242, 122, 77, .055), transparent 36%),
            linear-gradient(180deg, rgba(255,255,255,.030), rgba(255,255,255,.010)) !important;
    }

    body .stApp .mobile-wallet-hero:before {
        background:
            linear-gradient(115deg, rgba(255,255,255,.10), transparent 34%),
            radial-gradient(circle at 86% 4%, rgba(123,167,255,.08), transparent 44%) !important;
        opacity: .64 !important;
    }

    body .stApp .mobile-card-group-header {
        margin: 8px 0 14px !important;
        padding: 10px 12px !important;
        border-radius: 18px !important;
    }

    body .stApp .mobile-benefit-card {
        margin: 8px 0 12px !important;
        padding: 14px !important;
        border-radius: 20px !important;
    }

    body .stApp .history-summary-strip {
        display: grid !important;
        grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
        gap: 10px !important;
        margin: 10px 0 12px !important;
    }

    body .stApp .history-summary-strip > div,
    body .stApp .history-card {
        color: #f7f3fb !important;
        border: 1px solid rgba(255,255,255,.10) !important;
        background:
            radial-gradient(circle at 94% 4%, rgba(242,122,77,.10), transparent 38%),
            linear-gradient(145deg, rgba(255,255,255,.070), rgba(255,255,255,.024)),
            rgba(31, 30, 38, .94) !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.075), 0 10px 24px rgba(0,0,0,.24) !important;
    }

    body .stApp .history-summary-strip > div {
        border-radius: 16px !important;
        padding: 11px 12px !important;
    }

    body .stApp .history-summary-strip span,
    body .stApp .history-benefit-meta,
    body .stApp .history-row-footer,
    body .stApp .history-legend {
        color: #d7d0df !important;
        -webkit-text-fill-color: #d7d0df !important;
    }

    body .stApp .history-summary-strip span,
    body .stApp .history-summary-strip strong {
        display: block !important;
    }

    body .stApp .history-summary-strip strong {
        margin-top: 3px !important;
        font-size: 1.18rem !important;
        line-height: 1 !important;
    }

    body .stApp .history-summary-strip strong,
    body .stApp .history-benefit-name {
        color: #f7f3fb !important;
        -webkit-text-fill-color: #f7f3fb !important;
    }

    body .stApp .history-owner-heading {
        display: flex !important;
        align-items: baseline !important;
        justify-content: space-between !important;
        gap: 10px !important;
        margin: 18px 0 8px !important;
        padding: 0 2px !important;
    }

    body .stApp .history-owner-heading span {
        color: #f7f3fb !important;
        -webkit-text-fill-color: #f7f3fb !important;
        font-size: 1.05rem !important;
        font-weight: 900 !important;
        letter-spacing: 0 !important;
    }

    body .stApp .history-owner-heading small {
        color: #d7d0df !important;
        -webkit-text-fill-color: #d7d0df !important;
        font-size: .76rem !important;
        font-weight: 750 !important;
    }

    body .stApp .history-card {
        margin: 10px 0 13px !important;
        padding: 14px !important;
        border-radius: 20px !important;
        position: relative !important;
    }

    body .stApp .history-card-hidden {
        opacity: .44 !important;
        filter: grayscale(.88) saturate(.30) !important;
        border-style: dashed !important;
        background:
            linear-gradient(145deg, rgba(72,72,84,.34), rgba(38,38,48,.40)),
            rgba(24, 23, 30, .88) !important;
        box-shadow: none !important;
    }

    body .stApp .history-card-hidden:after {
        content: "Hidden" !important;
        position: absolute !important;
        top: 12px !important;
        right: 14px !important;
        color: #d7d0df !important;
        -webkit-text-fill-color: #d7d0df !important;
        border: 1px solid rgba(255,255,255,.10) !important;
        background: rgba(255,255,255,.060) !important;
        border-radius: 999px !important;
        padding: 4px 8px !important;
        font-size: .68rem !important;
        font-weight: 850 !important;
    }

    body .stApp .history-card-hidden .history-rate-pill {
        visibility: hidden !important;
    }

    body .stApp .history-card-hidden .history-cell-used,
    body .stApp .history-card-hidden .history-cell-partial,
    body .stApp .history-card-hidden .history-cell-missed,
    body .stApp .history-card-hidden .history-cell-open,
    body .stApp .history-card-hidden .history-cell-future,
    body .stApp .history-card-hidden .history-cell-untracked {
        color: rgba(215,208,223,.74) !important;
        -webkit-text-fill-color: rgba(215,208,223,.74) !important;
        background: rgba(255,255,255,.055) !important;
        border-color: rgba(255,255,255,.08) !important;
    }

    body .stApp .history-hidden-pill {
        color: #d7d0df !important;
        -webkit-text-fill-color: #d7d0df !important;
        border: 1px solid rgba(255,255,255,.10) !important;
        background: rgba(255,255,255,.045) !important;
        border-radius: 999px !important;
        margin-top: 6px !important;
        padding: 4px 8px !important;
        font-size: .68rem !important;
        font-weight: 800 !important;
        text-align: center !important;
    }

    body .stApp [class*="st-key-history_actions_"] {
        margin: -7px 0 10px !important;
    }

    body .stApp button[data-testid="stBaseButton-pills"],
    body .stApp button[kind="pills"] {
        color: #d7d0df !important;
        -webkit-text-fill-color: #d7d0df !important;
        border: 1px solid rgba(255,255,255,.12) !important;
        background: rgba(255,255,255,.052) !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.055), 0 1px 2px rgba(0,0,0,.18) !important;
    }

    body .stApp button[data-testid="stBaseButton-pills"] *,
    body .stApp button[kind="pills"] * {
        color: #d7d0df !important;
        -webkit-text-fill-color: #d7d0df !important;
    }

    body .stApp button[data-testid="stBaseButton-pillsActive"],
    body .stApp button[kind="pillsActive"] {
        color: #f7f3fb !important;
        -webkit-text-fill-color: #f7f3fb !important;
        border: 1px solid rgba(123,167,255,.42) !important;
        background:
            linear-gradient(180deg, rgba(123,167,255,.26), rgba(88,124,220,.18)),
            rgba(255,255,255,.070) !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.10), 0 4px 12px rgba(71,101,190,.20) !important;
    }

    body .stApp button[data-testid="stBaseButton-pillsActive"] *,
    body .stApp button[kind="pillsActive"] * {
        color: #f7f3fb !important;
        -webkit-text-fill-color: #f7f3fb !important;
    }

    body .stApp .history-card-top,
    body .stApp .history-title-row,
    body .stApp .history-row-footer,
    body .stApp .history-legend {
        display: flex !important;
        align-items: center !important;
    }

    body .stApp .history-card-top {
        justify-content: space-between !important;
        gap: 10px !important;
        margin-bottom: 12px !important;
    }

    body .stApp .history-title-row {
        gap: 10px !important;
        min-width: 0 !important;
    }

    body .stApp .history-title-row > div {
        min-width: 0 !important;
    }

    body .stApp .history-icon {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        flex: 0 0 auto !important;
        width: 32px !important;
        height: 32px !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,.12) !important;
        background:
            radial-gradient(circle at 35% 20%, rgba(255,255,255,.16), transparent 42%),
            linear-gradient(145deg, rgba(255,255,255,.095), rgba(255,255,255,.032)),
            rgba(36, 35, 45, .90) !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.11), 0 8px 18px rgba(0,0,0,.20) !important;
    }

    body .stApp .history-rate-pill {
        flex: 0 0 auto !important;
        color: #eef4ff !important;
        -webkit-text-fill-color: #eef4ff !important;
        border: 1px solid rgba(168,193,255,.24) !important;
        background: rgba(123,167,255,.15) !important;
        border-radius: 999px !important;
        padding: 6px 9px !important;
        font-size: .76rem !important;
        font-weight: 800 !important;
    }

    body .stApp .history-benefit-name {
        font-size: .98rem !important;
        font-weight: 850 !important;
        line-height: 1.18 !important;
    }

    body .stApp .history-benefit-meta {
        margin-top: 3px !important;
        font-size: .80rem !important;
        font-weight: 650 !important;
        line-height: 1.25 !important;
    }

    body .stApp .history-month-labels,
    body .stApp .history-grid {
        display: grid !important;
        grid-template-columns: repeat(12, minmax(20px, 1fr)) !important;
        gap: 5px !important;
    }

    body .stApp .history-month-labels {
        margin: 2px 0 5px !important;
    }

    body .stApp .history-month-labels span {
        color: #a9a1b5 !important;
        -webkit-text-fill-color: #a9a1b5 !important;
        text-align: center !important;
        font-size: .64rem !important;
        font-weight: 800 !important;
    }

    body .stApp .history-cell {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        aspect-ratio: 1 / 1 !important;
        min-height: 20px !important;
        border-radius: 7px !important;
        font-size: .68rem !important;
        font-weight: 900 !important;
        line-height: 1 !important;
        border: 1px solid transparent !important;
    }

    body .stApp .history-cell-used,
    body .stApp .history-dot-used {
        color: #052e22 !important;
        -webkit-text-fill-color: #052e22 !important;
        background: linear-gradient(180deg, #8ee6b2, #38c989) !important;
        border-color: rgba(142,230,178,.18) !important;
    }

    body .stApp .history-cell-partial,
    body .stApp .history-dot-partial {
        color: #3f2703 !important;
        -webkit-text-fill-color: #3f2703 !important;
        background: linear-gradient(180deg, #f8d982, #e7a83a) !important;
        border-color: rgba(248,217,130,.20) !important;
    }

    body .stApp .history-cell-missed,
    body .stApp .history-dot-missed {
        color: #3f1010 !important;
        -webkit-text-fill-color: #3f1010 !important;
        background: linear-gradient(180deg, #f4a0a0, #df6464) !important;
        border-color: rgba(244,160,160,.20) !important;
    }

    body .stApp .history-cell-open,
    body .stApp .history-dot-open {
        background: rgba(123,167,255,.20) !important;
        border-color: rgba(168,193,255,.20) !important;
    }

    body .stApp .history-cell-future {
        background: rgba(255,255,255,.060) !important;
        border-color: rgba(255,255,255,.085) !important;
    }

    body .stApp .history-cell-untracked {
        background: rgba(255,255,255,.026) !important;
        border-color: rgba(255,255,255,.046) !important;
    }

    body .stApp .history-row-footer,
    body .stApp .history-legend {
        gap: 10px !important;
        flex-wrap: wrap !important;
        margin-top: 10px !important;
        font-size: .74rem !important;
        font-weight: 750 !important;
    }

    body .stApp .history-dot {
        display: inline-flex !important;
        width: 10px !important;
        height: 10px !important;
        border-radius: 3px !important;
        margin-right: 5px !important;
        vertical-align: -1px !important;
    }

    @media (max-width: 640px) {
        body .stApp .history-summary-strip {
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
        }

        body .stApp .history-card {
            padding: 13px !important;
        }

        body .stApp .history-card-top {
            align-items: flex-start !important;
        }

        body .stApp .history-rate-pill {
            font-size: .68rem !important;
            padding: 5px 7px !important;
        }

        body .stApp .history-month-labels,
        body .stApp .history-grid {
            gap: 4px !important;
        }
    }

    body .stApp .benefit-title-row,
    body .stApp .mobile-benefit-title-row {
        display: flex !important;
        align-items: flex-start !important;
        gap: 10px !important;
        min-width: 0 !important;
    }

    body .stApp .benefit-title-row > div,
    body .stApp .mobile-benefit-title-row > div {
        min-width: 0 !important;
    }

    body .stApp .benefit-visual-cue,
    body .stApp .mobile-benefit-visual,
    body .stApp .mobile-section-emoji {
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        flex: 0 0 auto !important;
        width: 30px !important;
        height: 30px !important;
        border-radius: 12px !important;
        border: 1px solid rgba(255,255,255,.12) !important;
        background:
            radial-gradient(circle at 35% 20%, rgba(255,255,255,.16), transparent 42%),
            linear-gradient(145deg, rgba(255,255,255,.095), rgba(255,255,255,.032)),
            rgba(36, 35, 45, .90) !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.11), 0 8px 18px rgba(0,0,0,.20) !important;
        font-size: 1rem !important;
        line-height: 1 !important;
        -webkit-text-fill-color: currentColor !important;
    }

    body .stApp .mobile-section-heading {
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
    }

    body .stApp .mobile-section-heading:before {
        content: none !important;
        display: none !important;
    }

    body .stApp .mobile-section-emoji {
        width: 24px !important;
        height: 24px !important;
        border-radius: 9px !important;
        font-size: .86rem !important;
    }

    body .stApp .mobile-benefit-facts {
        gap: 8px !important;
        margin-top: 12px !important;
    }

    body .stApp .mobile-benefit-facts > div {
        min-height: 72px !important;
        padding: 10px 11px !important;
        border-radius: 16px !important;
    }

    body .stApp .mobile-detail-note {
        color: #f7f3fb !important;
        border: 1px solid rgba(255,255,255,.11) !important;
        background:
            radial-gradient(circle at 94% 4%, rgba(242,122,77,.14), transparent 38%),
            linear-gradient(145deg, rgba(255,255,255,.075), rgba(255,255,255,.026)),
            rgba(28, 27, 35, .96) !important;
        border-radius: 18px !important;
        margin: 12px 0 6px !important;
        padding: 13px 14px !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.08), 0 12px 24px rgba(0,0,0,.26) !important;
    }

    body .stApp .mobile-detail-note,
    body .stApp .mobile-detail-note * {
        color: #f7f3fb !important;
        -webkit-text-fill-color: #f7f3fb !important;
    }

    body .stApp .mobile-detail-note p {
        color: #d7d0df !important;
        -webkit-text-fill-color: #d7d0df !important;
    }

    body .stApp .mobile-adjust-summary {
        color: #d7d0df !important;
        -webkit-text-fill-color: #d7d0df !important;
        border: 1px solid rgba(255,255,255,.10) !important;
        background:
            linear-gradient(145deg, rgba(255,255,255,.072), rgba(255,255,255,.024)),
            rgba(31, 30, 38, .94) !important;
        border-radius: 16px !important;
        margin: 12px 0 10px !important;
        padding: 11px 13px !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.075), 0 8px 18px rgba(0,0,0,.20) !important;
    }

    body .stApp .mobile-empty-state {
        color: #cfc8d8 !important;
        -webkit-text-fill-color: #cfc8d8 !important;
        border: 1px solid rgba(255,255,255,.10) !important;
        background:
            linear-gradient(145deg, rgba(255,255,255,.060), rgba(255,255,255,.020)),
            rgba(30, 29, 37, .88) !important;
        border-radius: 16px !important;
        margin: 8px 0 12px !important;
        padding: 10px 12px !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.065) !important;
    }

    body .stApp .st-key-mobile_dashboard div[data-testid="stExpander"] [data-testid="stMarkdownContainer"]:has(.mobile-section-heading),
    body .stApp .st-key-mobile_dashboard div[data-testid="stExpander"] .mobile-section-heading {
        margin-top: 4px !important;
        margin-bottom: 2px !important;
    }

    body .stApp .st-key-mobile_dashboard div[data-testid="stExpander"] [data-testid="stVerticalBlock"] {
        gap: 8px !important;
        row-gap: 8px !important;
    }

    body .stApp .st-key-mobile_dashboard div[data-testid="stExpander"] div[data-testid="stExpander"] {
        margin: 6px 0 10px !important;
    }

    body .stApp [data-testid="stSlider"] label,
    body .stApp [data-testid="stSlider"] label *,
    body .stApp [data-testid="stSlider"] [data-testid="stTickBar"],
    body .stApp [data-testid="stSlider"] [data-testid="stTickBar"] * {
        color: #f7f3fb !important;
        -webkit-text-fill-color: #f7f3fb !important;
    }

    body .stApp [data-testid="stSlider"] [data-baseweb="slider"] > div {
        background:
            linear-gradient(180deg, rgba(121, 128, 151, .42), rgba(72, 76, 92, .46)) !important;
        border-radius: 999px !important;
        box-shadow:
            inset 0 1px 2px rgba(0,0,0,.28),
            inset 0 -1px 0 rgba(255,255,255,.050) !important;
    }

    body .stApp [data-testid="stSlider"] [data-baseweb="slider"] [aria-valuenow] {
        position: relative !important;
        z-index: 3 !important;
        background: #7ba7ff !important;
        border-color: #eef4ff !important;
        box-shadow:
            0 0 0 4px rgba(123,167,255,.18),
            0 8px 18px rgba(0,0,0,.28) !important;
    }

    body .stApp [data-testid="stSlider"] [data-baseweb="slider"] > div > div {
        background-color: transparent !important;
    }

    body .stApp [data-testid="stSlider"] [data-baseweb="slider"] > div > div > div > div:last-child,
    body .stApp [data-testid="stSlider"] [data-baseweb="slider"] div[class*="st-c7"] {
        opacity: 1 !important;
        filter: none !important;
        border-radius: 999px !important;
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,.22),
            0 0 14px rgba(123,167,255,.16) !important;
    }

    body .stApp [data-testid="stSlider"] [data-testid="stSliderTickBar"],
    body .stApp [data-testid="stSlider"] [data-testid="stSliderTickBar"] [data-testid="stMarkdownContainer"] {
        background: transparent !important;
    }

    body .stApp div[data-testid="stButton"] button[kind="primary"],
    body .stApp div[data-testid="stButton"] button[data-testid="baseButton-primary"],
    body .stApp .st-key-mobile_dashboard div[data-testid="stButton"] button[kind="primary"],
    body .stApp .st-key-mobile_dashboard div[data-testid="stButton"] button[data-testid="baseButton-primary"] {
        color: #eef4ff !important;
        -webkit-text-fill-color: #eef4ff !important;
        border-color: rgba(168, 193, 255, .24) !important;
        background:
            radial-gradient(circle at 28% 0%, rgba(168, 193, 255, .20), transparent 42%),
            linear-gradient(180deg, rgba(86, 104, 162, .72), rgba(49, 53, 76, .94)) !important;
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,.16),
            inset 0 -1px 0 rgba(0,0,0,.22),
            0 10px 22px rgba(0,0,0,.22) !important;
        text-shadow: 0 1px 1px rgba(0,0,0,.22) !important;
    }

    body .stApp div[data-testid="stButton"] button[kind="primary"]:hover,
    body .stApp div[data-testid="stButton"] button[data-testid="baseButton-primary"]:hover,
    body .stApp .st-key-mobile_dashboard div[data-testid="stButton"] button[kind="primary"]:hover,
    body .stApp .st-key-mobile_dashboard div[data-testid="stButton"] button[data-testid="baseButton-primary"]:hover {
        border-color: rgba(186, 207, 255, .34) !important;
        background:
            radial-gradient(circle at 28% 0%, rgba(186, 207, 255, .24), transparent 42%),
            linear-gradient(180deg, rgba(96, 116, 176, .78), rgba(54, 58, 82, .96)) !important;
        box-shadow:
            inset 0 1px 0 rgba(255,255,255,.18),
            0 12px 24px rgba(0,0,0,.26) !important;
    }

    body .stApp section[data-testid="stSidebar"] {
        color: #f7f3fb !important;
        background:
            radial-gradient(circle at 18% 8%, rgba(123,167,255,.16), transparent 15rem),
            radial-gradient(circle at 84% 22%, rgba(242,122,77,.10), transparent 16rem),
            linear-gradient(180deg, rgba(33,32,42,.94), rgba(18,17,24,.96)) !important;
        border-right: 1px solid rgba(255,255,255,.10) !important;
        box-shadow:
            14px 0 34px rgba(0,0,0,.38),
            inset -1px 0 0 rgba(255,255,255,.06) !important;
        backdrop-filter: blur(28px) saturate(1.12) !important;
        -webkit-backdrop-filter: blur(28px) saturate(1.12) !important;
    }

    body .stApp section[data-testid="stSidebar"] > div {
        background: linear-gradient(180deg, rgba(255,255,255,.035), rgba(255,255,255,.010)) !important;
    }

    body .stApp section[data-testid="stSidebar"] h1,
    body .stApp section[data-testid="stSidebar"] h2,
    body .stApp section[data-testid="stSidebar"] h3,
    body .stApp section[data-testid="stSidebar"] p,
    body .stApp section[data-testid="stSidebar"] span,
    body .stApp section[data-testid="stSidebar"] label,
    body .stApp section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
    body .stApp section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] * {
        color: #f7f3fb !important;
        -webkit-text-fill-color: #f7f3fb !important;
    }

    body .stApp section[data-testid="stSidebar"] .sidebar-brand,
    body .stApp section[data-testid="stSidebar"] .sidebar-data-summary {
        border-color: rgba(255,255,255,.14) !important;
        background:
            linear-gradient(145deg, rgba(255,255,255,.085), rgba(255,255,255,.030)),
            rgba(34,33,43,.76) !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.10), 0 10px 22px rgba(0,0,0,.22) !important;
    }

    body .stApp section[data-testid="stSidebar"] [data-baseweb="radio"] {
        color: #d7d0df !important;
        border-color: rgba(255,255,255,.10) !important;
        background: rgba(255,255,255,.045) !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.06) !important;
    }

    body .stApp section[data-testid="stSidebar"] [data-baseweb="radio"]:has(input:checked) {
        color: #f7f3fb !important;
        border-color: rgba(168,193,255,.30) !important;
        background: rgba(123,167,255,.16) !important;
        box-shadow: inset 0 1px 0 rgba(255,255,255,.12), 0 8px 18px rgba(0,0,0,.24) !important;
    }
    </style>
    """


def inject_theme_styles(theme: str) -> None:
    st.markdown(theme_override_css(theme), unsafe_allow_html=True)


def apply_theme_selection(source_key: str) -> None:
    selected_theme_label = st.session_state.get(source_key, "Dark Wallet")
    selected_theme = THEME_OPTIONS.get(str(selected_theme_label), "dark")
    st.session_state["app_theme"] = selected_theme
    save_ui_settings(selected_theme)


def render_theme_selector(key: str, *, horizontal: bool = False, label: str = "Appearance") -> None:
    theme = active_app_theme()
    theme_label = THEME_LABELS.get(theme, "Dark Wallet")
    st.radio(
        label,
        list(THEME_OPTIONS.keys()),
        index=list(THEME_OPTIONS.keys()).index(theme_label),
        horizontal=horizontal,
        key=key,
        on_change=apply_theme_selection,
        args=(key,),
    )


def format_amount(value: object) -> str:
    amount = normalize_money(value)
    return f"${amount:,.0f}" if amount == round(amount) else f"${amount:,.2f}"


def clean_display(value: object, fallback: str = "\u2014") -> str:
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


BENEFIT_VISUAL_PATTERNS = [
    (["hotel", "fhr", "resort", "hilton", "hyatt", "marriott"], "🏨"),
    (["resy", "dining", "restaurant", "doordash", "grubhub", "uber eats", "coffee", "wine"], "🍽️"),
    (["uber", "rideshare", "lyft", "taxi"], "🚗"),
    (["airline", "flight", "delta", "united", "southwest"], "✈️"),
    (["saks", "shopping", "shop", "store"], "🛍️"),
    (["lululemon", "wellness", "yoga"], "🧘"),
    (["stubhub", "viagogo", "ticket", "entertainment", "disney", "hulu", "espn"], "🎟️"),
    (["whoop", "fitness", "gym"], "💪"),
    (["global entry", "tsa", "clear"], "🛂"),
    (["grocery", "instacart"], "🛒"),
    (["fee", "annual"], "💳"),
    (["credit"], "💳"),
]


SECTION_VISUALS = {
    "priority reminders": "⚡",
    "not used this month": "🗓️",
    "partially used": "◐",
    "upcoming next": "⏳",
    "available now": "✅",
    "upcoming": "⏳",
    "completed / hidden": "🗂️",
    "completed": "✅",
    "hidden": "🫥",
    "annual fees": "💳",
}

MONTH_LABELS = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
HISTORY_FREQUENCIES = ["Monthly", "Quarterly", "Semiannual", "Annual"]


def benefit_visual_cue(row: pd.Series) -> str:
    fields = [
        row.get("benefit_name"),
        row.get("category"),
        row.get("benefit_type"),
        row.get("card_name"),
        row.get("notes"),
    ]
    text = " ".join(normalize_text(value) for value in fields).lower()
    for keywords, icon in BENEFIT_VISUAL_PATTERNS:
        if any(keyword in text for keyword in keywords):
            return icon
    return category_icon(row.get("category"))


def section_visual_cue(title: str) -> str:
    text = normalize_text(title).lower()
    if text in SECTION_VISUALS:
        return SECTION_VISUALS[text]
    return category_icon(title)


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


def render_dashboard_kpis(
    active_count: int,
    expiring_count: int,
    completed_count: int,
    remaining_value: float,
    annual_fees: float,
) -> None:
    """Render the desktop KPI strip with a deliberate finance-dashboard hierarchy."""
    expiring_tone = "calm" if expiring_count == 0 else "warning"
    st.markdown(
        f"""
        <div class="dashboard-kpi-grid">
            <div class="dashboard-kpi-card secondary">
                <span>Active benefits</span>
                <strong>{active_count}</strong>
            </div>
            <div class="dashboard-kpi-card {expiring_tone}">
                <span>Expiring soon</span>
                <strong>{expiring_count}</strong>
            </div>
            <div class="dashboard-kpi-card secondary">
                <span>Completed</span>
                <strong>{completed_count}</strong>
            </div>
            <div class="dashboard-kpi-card emphasis">
                <span>Value remaining</span>
                <strong>{format_amount(remaining_value)}</strong>
            </div>
            <div class="dashboard-kpi-card emphasis fee">
                <span>Annual fees</span>
                <strong>{format_amount(annual_fees)}</strong>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def category_badge(category: object) -> str:
    label = clean_display(category, "Other")
    return f'<span class="chip">{escape(category_icon(label))} {escape(label)}</span>'


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


@st.cache_data(show_spinner=False)
def _cached_image_data_uri(path_text: str, modified_ns: int) -> str:
    mime_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
        ".avif": "image/avif",
        ".svg": "image/svg+xml",
    }
    path = Path(path_text)
    mime_type = mime_types.get(path.suffix.lower(), "image/png")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def card_image_data_uri(path: Path) -> str:
    return _cached_image_data_uri(str(path), path.stat().st_mtime_ns)


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
    display_label = "Available" if label == "Not Used" else "Hidden" if label == "Ignored" else label
    return f'<span class="badge" style="background:{background};color:{color};">{escape(display_label)}</span>'


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

    today = pd.Timestamp.today().date()
    fee_date = annual_fee_date(card.get("open_date"), today)
    if not fee_date:
        return "Fee date not set"

    days = (fee_date - today).days
    return f"Annual fee in {days} days ({fee_date.strftime('%b')} {fee_date.day})"


def query_param_flag(name: str) -> bool | None:
    try:
        value = st.query_params.get(name)
    except Exception:
        return None

    if isinstance(value, list):
        value = value[0] if value else ""
    text = normalize_text(value).lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return None


def is_mobile_request() -> bool:
    override = query_param_flag("mobile")
    if override is not None:
        return override

    try:
        headers = st.context.headers
        user_agent = headers.get("user-agent", "") if hasattr(headers, "get") else ""
    except Exception:
        return False

    agent = user_agent.lower()
    if not agent:
        return False
    if any(token in agent for token in ["ipad", "tablet", "kindle"]):
        return False
    if any(token in agent for token in ["iphone", "ipod", "windows phone", "opera mini"]):
        return True
    return "android" in agent and "mobile" in agent


def force_mobile_dashboard_css() -> None:
    st.markdown(
        """
        <style>
        .st-key-mobile_dashboard,
        [class*="st-key-mobile_dashboard"] {
            display: block !important;
        }

        .st-key-desktop_dashboard,
        [class*="st-key-desktop_dashboard"] {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def mobile_attention_benefits(active: pd.DataFrame) -> pd.DataFrame:
    if active.empty:
        return active.copy()

    due = active.copy()
    due["_attention_window"] = due["frequency"].map(benefit_attention_window)
    due["_days_until_expiration"] = pd.to_numeric(due["days_until_expiration"], errors="coerce")
    remaining = due["remaining_amount"].apply(normalize_money) if "remaining_amount" in due else 0
    eligible_status = due["status"].isin(["Not Used", "Partially Used"])
    mask = (
        eligible_status
        & (~due["is_upcoming"])
        & due["_attention_window"].gt(0)
        & due["_days_until_expiration"].ge(0)
        & due["_days_until_expiration"].le(due["_attention_window"])
        & remaining.gt(0)
    )
    return due[mask].drop(columns=["_attention_window", "_days_until_expiration"]).copy()


def mobile_monthly_not_used(active: pd.DataFrame) -> pd.DataFrame:
    if active.empty:
        return active.copy()

    frequency = active["frequency"].fillna("").astype(str).str.lower()
    remaining = active["remaining_amount"].apply(normalize_money) if "remaining_amount" in active else 0
    return active[
        active["status"].eq("Not Used")
        & frequency.str.contains("monthly", na=False)
        & (~active["is_upcoming"])
        & remaining.gt(0)
    ].copy()


def sort_mobile_benefits(benefits: pd.DataFrame) -> pd.DataFrame:
    if benefits.empty:
        return benefits.copy()

    sorted_benefits = benefits.copy()
    priority_rank = {"High": 0, "Medium": 1, "Low": 2}
    sorted_benefits["_priority_rank"] = sorted_benefits["priority"].map(priority_rank).fillna(3)
    sorted_benefits["_days_until_expiration"] = pd.to_numeric(
        sorted_benefits["days_until_expiration"],
        errors="coerce",
    ).fillna(99999)
    sorted_benefits = sorted_benefits.sort_values(
        ["_days_until_expiration", "_priority_rank", "card_name", "benefit_name"],
        na_position="last",
    )
    return sorted_benefits.drop(columns=["_priority_rank", "_days_until_expiration"])


def annual_fee_reminders(cards: pd.DataFrame, within_days: int = 30) -> pd.DataFrame:
    rows = []
    if cards.empty:
        return pd.DataFrame(rows)

    today = pd.Timestamp.today().date()
    for _, card in cards.iterrows():
        if clean_display(card.get("status"), "").lower() == "closed":
            continue

        annual_fee = normalize_money(card.get("annual_fee"))
        if annual_fee <= 0:
            continue

        fee_date = annual_fee_date(card.get("open_date"), today)
        if not fee_date:
            continue

        days_left = (fee_date - today).days
        if 0 <= days_left <= within_days:
            rows.append(
                {
                    **card.to_dict(),
                    "annual_fee_date": fee_date.isoformat(),
                    "days_left": days_left,
                }
            )

    reminders = pd.DataFrame(rows)
    if reminders.empty:
        return reminders
    return reminders.sort_values(["days_left", "card_name"])


def cycle_year(value: object) -> int | None:
    text = normalize_text(value)
    if len(text) >= 4 and text[:4].isdigit():
        return int(text[:4])
    parsed = pd.to_datetime(text, errors="coerce")
    if pd.isna(parsed):
        return None
    return int(parsed.year)


def available_history_years(benefits: pd.DataFrame, usage: pd.DataFrame) -> list[int]:
    years: set[int] = set()
    for column in ["cycle_period", "used_date"]:
        if column in usage:
            for value in usage[column].dropna():
                year = cycle_year(value)
                if year:
                    years.add(year)
    for column in ["current_cycle", "expiration_date", "cycle_start_date"]:
        if column in benefits:
            for value in benefits[column].dropna():
                year = cycle_year(value)
                if year:
                    years.add(year)
    if not years:
        years.add(pd.Timestamp.today().year)
    return sorted(years)


def cycle_start_from_text(value: object) -> pd.Timestamp | None:
    text = normalize_text(value)
    year = cycle_year(text)
    if not year:
        parsed = pd.to_datetime(text, errors="coerce")
        return None if pd.isna(parsed) else pd.Timestamp(parsed).replace(day=1)
    if "-Q" in text.upper():
        quarter = text.upper().split("-Q", 1)[1][:1]
        if quarter.isdigit() and 1 <= int(quarter) <= 4:
            return pd.Timestamp(year=year, month=(int(quarter) - 1) * 3 + 1, day=1)
    if "-H" in text.upper():
        half = text.upper().split("-H", 1)[1][:1]
        if half == "1":
            return pd.Timestamp(year=year, month=1, day=1)
        if half == "2":
            return pd.Timestamp(year=year, month=7, day=1)
    if len(text) >= 7 and text[4] == "-":
        parsed = pd.to_datetime(f"{text[:7]}-01", errors="coerce")
        if not pd.isna(parsed):
            return pd.Timestamp(parsed)
    return pd.Timestamp(year=year, month=1, day=1)


def history_tracking_start(benefits: pd.DataFrame, usage: pd.DataFrame) -> pd.Timestamp:
    starts: list[pd.Timestamp] = []
    if "used_date" in usage:
        for value in usage["used_date"].dropna():
            parsed = pd.to_datetime(value, errors="coerce")
            if not pd.isna(parsed):
                starts.append(pd.Timestamp(parsed).replace(day=1))
    if starts:
        return min(starts)

    if "cycle_period" in usage:
        for value in usage["cycle_period"].dropna():
            parsed = cycle_start_from_text(value)
            if parsed is not None:
                starts.append(parsed)
    if starts:
        return min(starts)

    if "cycle_start_date" in benefits:
        for value in benefits["cycle_start_date"].dropna():
            parsed = pd.to_datetime(value, errors="coerce")
            if not pd.isna(parsed):
                starts.append(pd.Timestamp(parsed).replace(day=1))
    return min(starts) if starts else pd.Timestamp.today().replace(day=1)


def usage_cycle_lookup(usage: pd.DataFrame) -> dict[tuple[str, str], dict[str, object]]:
    if usage.empty:
        return {}

    lookup: dict[tuple[str, str], dict[str, object]] = {}
    for _, record in usage.iterrows():
        benefit_id = clean_display(record.get("benefit_id"), "")
        cycle = clean_display(record.get("cycle_period"), "")
        if not benefit_id or not cycle:
            continue
        key = (benefit_id, cycle)
        entry = lookup.setdefault(key, {"amount": 0.0, "fully_used": False})
        entry["amount"] = float(entry["amount"]) + normalize_money(record.get("used_amount"))
        entry["fully_used"] = bool(entry["fully_used"]) or clean_display(record.get("fully_used"), "").lower() == "yes"
    return lookup


def benefit_history_group(row: pd.Series, year: int, month: int) -> tuple[str, list[int], pd.Timestamp] | None:
    frequency = clean_display(row.get("frequency"), "").lower()
    cycle = clean_display(row.get("current_cycle"), "")
    name = clean_display(row.get("benefit_name"), "")
    expiration = pd.to_datetime(row.get("expiration_date"), errors="coerce")

    if "month" in frequency:
        end = pd.Timestamp(year=year, month=month, day=1) + pd.offsets.MonthEnd(0)
        return f"{year}-{month:02d}", [month], end

    if "quarter" in frequency:
        quarter = None
        marker_text = f"{cycle} {name}".upper()
        for possible in [1, 2, 3, 4]:
            if f"Q{possible}" in marker_text:
                quarter = possible
                break
        if quarter is None and not pd.isna(expiration):
            quarter = int((pd.Timestamp(expiration).month - 1) / 3) + 1
        if quarter is None or int((month - 1) / 3) + 1 != quarter:
            return None
        months = list(range((quarter - 1) * 3 + 1, quarter * 3 + 1))
        end = pd.Timestamp(year=year, month=months[-1], day=1) + pd.offsets.MonthEnd(0)
        return f"{year}-Q{quarter}", months, end

    if "semi" in frequency or "bi" in frequency:
        half = None
        marker_text = f"{cycle} {name}".upper()
        if "H1" in marker_text:
            half = 1
        elif "H2" in marker_text:
            half = 2
        elif not pd.isna(expiration):
            half = 1 if pd.Timestamp(expiration).month <= 6 else 2
        if half is None or (month <= 6 and half != 1) or (month >= 7 and half != 2):
            return None
        months = list(range(1, 7)) if half == 1 else list(range(7, 13))
        end = pd.Timestamp(year=year, month=months[-1], day=1) + pd.offsets.MonthEnd(0)
        return f"{year}-H{half}", months, end

    if "annual" in frequency or "year" in frequency:
        end = pd.Timestamp(year=year, month=12, day=31)
        return f"{year}", list(range(1, 13)), end

    return None


def history_frequency_kind(value: object) -> str:
    text = clean_display(value, "").lower()
    if "month" in text:
        return "Monthly"
    if "quarter" in text:
        return "Quarterly"
    if "semi" in text or "bi" in text:
        return "Semiannual"
    if "annual" in text or "year" in text:
        return "Annual"
    return "Other"


def history_cell_state(
    row: pd.Series,
    year: int,
    month: int,
    lookup: dict[tuple[str, str], dict[str, object]],
    tracking_start: pd.Timestamp,
    today: pd.Timestamp,
) -> tuple[str, str]:
    group = benefit_history_group(row, year, month)
    if group is None:
        return "future", "outside this benefit cycle"

    cycle_key, _, period_end = group
    benefit_id = clean_display(row.get("benefit_id"), "")
    face_value = normalize_money(row.get("face_value"))
    usage_entry = lookup.get((benefit_id, cycle_key), {"amount": 0.0, "fully_used": False})
    amount = normalize_money(usage_entry.get("amount"))
    fully_used = bool(usage_entry.get("fully_used"))

    if amount <= 0 and clean_display(row.get("current_cycle"), "") == cycle_key:
        amount = normalize_money(row.get("used_amount"))
        fully_used = fully_used or clean_display(row.get("status"), "") == "Used"

    if fully_used or (face_value > 0 and amount >= face_value):
        return "used", f"{format_amount(amount)} used"
    if amount > 0:
        return "partial", f"{format_amount(amount)} partially used"
    if period_end < tracking_start:
        return "untracked", "not tracked yet"
    if period_end < today.normalize():
        return "missed", "missed"
    return "open", "still available"


def history_cell_symbol(state: str) -> str:
    symbols = {
        "used": "Y",
        "partial": "~",
        "missed": "X",
        "open": "",
        "future": "",
        "untracked": "",
    }
    return symbols.get(state, "")


def history_row_stats(states: list[str]) -> tuple[int, int, int]:
    used = sum(1 for state in states if state == "used")
    partial = sum(1 for state in states if state == "partial")
    missed = sum(1 for state in states if state == "missed")
    return used, partial, missed


def render_history_card(
    row: pd.Series,
    year: int,
    lookup: dict[tuple[str, str], dict[str, object]],
    tracking_start: pd.Timestamp,
    today: pd.Timestamp,
    *,
    hidden: bool = False,
    mobile: bool = False,
) -> None:
    states: list[str] = []
    cells = []
    for month in range(1, 13):
        state, detail = history_cell_state(row, year, month, lookup, tracking_start, today)
        states.append(state)
        title = f"{MONTH_NAMES[month - 1]} {year}: {detail}"
        cells.append(
            f'<span class="history-cell history-cell-{state}" title="{escape(title)}" aria-label="{escape(title)}">'
            f"{escape(history_cell_symbol(state))}</span>"
        )

    used, partial, missed = history_row_stats(states)
    closed = used + partial + missed
    rate = int(round(((used + partial) / closed) * 100)) if closed else 0
    visual = benefit_visual_cue(row)
    name = clean_display(row.get("benefit_name"), "Unnamed benefit")
    card = clean_display(row.get("card_name"), "Card not set")
    owner = clean_display(row.get("owner"), "")
    frequency = clean_display(row.get("frequency"), "Benefit")
    face_value = format_amount(row.get("face_value"))
    owner_text = f" - {escape(owner)}" if owner else ""
    hidden_class = " history-card-hidden" if hidden else ""

    st.markdown(
        f"""
        <div class="history-card{hidden_class}">
            <div class="history-card-top">
                <div class="history-title-row">
                    <span class="history-icon" aria-hidden="true">{escape(visual)}</span>
                    <div>
                        <div class="history-benefit-name">{escape(name)}</div>
                        <div class="history-benefit-meta">{escape(card)}{owner_text} - {escape(frequency)} - {face_value}</div>
                    </div>
                </div>
                <div class="history-rate-pill">{rate}% captured</div>
            </div>
            <div class="history-month-labels">
                {"".join(f'<span>{label}</span>' for label in MONTH_LABELS)}
            </div>
            <div class="history-grid">
                {"".join(cells)}
            </div>
            <div class="history-row-footer">
                <span>{used} used</span>
                <span>{partial} partial</span>
                <span>{missed} missed</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    benefit_id = clean_display(row.get("benefit_id"), "")
    if not benefit_id:
        return
    safe_key = benefit_id.replace(" ", "_").replace("-", "_").replace("/", "_")
    with st.container(key=f"history_actions_{safe_key}"):
        if mobile:
            spacer_col, action_col = st.columns([2.3, 0.9])
            with action_col:
                if hidden:
                    if st.button("Show", key=f"history_restore_{safe_key}", use_container_width=True):
                        restore_to_history(benefit_id)
                else:
                    if st.button("Hide", key=f"history_hide_{safe_key}", use_container_width=True):
                        hide_from_history(benefit_id)
        else:
            spacer_col, action_col = st.columns([3.5, 1.1])
            with action_col:
                if hidden:
                    if st.button("Show in History", key=f"history_restore_{safe_key}", use_container_width=True):
                        restore_to_history(benefit_id)
                else:
                    if st.button("Hide", key=f"history_hide_{safe_key}", use_container_width=True):
                        hide_from_history(benefit_id)


def show_usage_history_view(benefits: pd.DataFrame, usage: pd.DataFrame, *, mobile: bool = False) -> None:
    if benefits.empty:
        st.markdown('<div class="mobile-empty-state">No benefits to analyze yet.</div>', unsafe_allow_html=True)
        return

    recurring = benefits[
        benefits["frequency"].fillna("").astype(str).str.lower().str.contains("month|quarter|semi|annual|year", na=False)
    ].copy()
    recurring = recurring[recurring["status"].fillna("").astype(str) != "Ignored"]
    if recurring.empty:
        st.markdown('<div class="mobile-empty-state">No recurring benefits to show yet.</div>', unsafe_allow_html=True)
        return

    years = available_history_years(recurring, usage)
    current_year = pd.Timestamp.today().year
    default_year_index = years.index(current_year) if current_year in years else len(years) - 1
    hidden_ids = history_hidden_benefit_ids()
    owner_options = ["All owners"] + sorted([owner for owner in recurring["owner"].dropna().unique() if normalize_text(owner)])

    filter_container = st.container(key="mobile_history_filters" if mobile else "desktop_history_filters")
    with filter_container:
        if mobile:
            if len(years) <= 4:
                selected_year = st.pills(
                    "Year",
                    years,
                    default=years[default_year_index],
                    required=True,
                    key="mobile_history_year_pills",
                )
            else:
                selected_year = st.selectbox("Year", years, index=default_year_index, key="mobile_history_year")
            selected_frequency = st.pills(
                "Frequency",
                ["All"] + HISTORY_FREQUENCIES,
                default="All",
                required=True,
                key="mobile_history_frequency_pills",
            )
            selected_owner = st.pills(
                "Owner",
                owner_options,
                default="All owners",
                required=True,
                key="mobile_history_owner_pills",
            )
            card_source = recurring if selected_owner == "All owners" else recurring[recurring["owner"] == selected_owner]
            card_options = ["All cards"] + sorted([card for card in card_source["card_name"].dropna().unique() if normalize_text(card)])
            if len(card_options) <= 16:
                selected_card = st.pills(
                    "Card",
                    card_options,
                    default="All cards",
                    required=True,
                    key="mobile_history_card_pills",
                )
            else:
                selected_card = st.selectbox("Card", card_options, key="mobile_history_card")
            show_history_hidden = st.toggle("Show hidden", value=False, key="mobile_history_show_hidden")
        else:
            year_col, frequency_col, owner_col, card_col, hidden_col = st.columns([0.82, 1.12, 1.14, 1.72, 0.92])
            if len(years) <= 4:
                selected_year = year_col.pills(
                    "Year",
                    years,
                    default=years[default_year_index],
                    required=True,
                    key="desktop_history_year_pills",
                )
            else:
                selected_year = year_col.selectbox("Year", years, index=default_year_index, key="desktop_history_year")
            selected_frequency = frequency_col.pills(
                "Frequency",
                ["All"] + HISTORY_FREQUENCIES,
                default="All",
                required=True,
                key="desktop_history_frequency_pills",
            )
            selected_owner = owner_col.pills(
                "Owner",
                owner_options,
                default="All owners",
                required=True,
                key="desktop_history_owner_pills",
            )
            card_source = recurring if selected_owner == "All owners" else recurring[recurring["owner"] == selected_owner]
            card_options = ["All cards"] + sorted([card for card in card_source["card_name"].dropna().unique() if normalize_text(card)])
            if len(card_options) <= 16:
                selected_card = card_col.pills(
                    "Card",
                    card_options,
                    default="All cards",
                    required=True,
                    key="desktop_history_card_pills",
                )
            else:
                selected_card = card_col.selectbox("Card", card_options, key="desktop_history_card")
            show_history_hidden = hidden_col.toggle("Show hidden", value=False, key="desktop_history_show_hidden")

    visible = recurring.copy()
    if not show_history_hidden and hidden_ids:
        visible = visible[~visible["benefit_id"].astype(str).isin(hidden_ids)]
    if selected_frequency != "All":
        visible = visible[visible["frequency"].map(history_frequency_kind) == selected_frequency]
    if selected_owner != "All owners":
        visible = visible[visible["owner"] == selected_owner]
    if selected_card != "All cards":
        visible = visible[visible["card_name"] == selected_card]

    lookup = usage_cycle_lookup(usage)
    tracking_start = history_tracking_start(recurring, usage)
    today = pd.Timestamp.today()

    all_states: list[str] = []
    for _, row in visible.iterrows():
        for month in range(1, 13):
            state, _ = history_cell_state(row, int(selected_year), month, lookup, tracking_start, today)
            all_states.append(state)
    used = sum(1 for state in all_states if state == "used")
    partial = sum(1 for state in all_states if state == "partial")
    missed = sum(1 for state in all_states if state == "missed")
    closed = used + partial + missed
    rate = int(round(((used + partial) / closed) * 100)) if closed else 0

    st.markdown(
        f"""
        <div class="history-summary-strip">
            <div><span>Captured rate</span><strong>{rate}%</strong></div>
            <div><span>Used cycles</span><strong>{used}</strong></div>
            <div><span>Partial cycles</span><strong>{partial}</strong></div>
            <div><span>Missed cycles</span><strong>{missed}</strong></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div class="history-legend">
            <span><i class="history-dot history-dot-used"></i>Used</span>
            <span><i class="history-dot history-dot-partial"></i>Partial</span>
            <span><i class="history-dot history-dot-missed"></i>Missed</span>
            <span><i class="history-dot history-dot-open"></i>Open/future</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if visible.empty:
        st.markdown('<div class="mobile-empty-state">No benefits match this filter.</div>', unsafe_allow_html=True)
        return

    visible = visible.copy()
    visible["_history_owner"] = visible["owner"].map(lambda value: clean_display(value, "Unassigned"))
    for owner in sorted(visible["_history_owner"].dropna().unique()):
        owner_group = visible[visible["_history_owner"] == owner]
        if owner_group.empty:
            continue
        st.markdown(
            f"""
            <div class="history-owner-heading">
                <span>{escape(owner)}</span>
                <small>{len(owner_group)} benefits</small>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for _, row in owner_group.sort_values(["card_name", "frequency", "benefit_name"]).iterrows():
            benefit_id = clean_display(row.get("benefit_id"), "")
            render_history_card(
                row,
                int(selected_year),
                lookup,
                tracking_start,
                today,
                hidden=benefit_id in hidden_ids,
                mobile=mobile,
            )


def benefit_summary_label(row: pd.Series) -> str:
    name = clean_display(row.get("benefit_name"))
    visual = benefit_visual_cue(row)
    status = clean_display(row.get("status"), "Not Used")
    upcoming = bool(row.get("is_upcoming", False))
    start_label = date_label(row.get("cycle_start_date"))
    due_text = f"Starts {start_label}" if upcoming and start_label else due_text_from_days(row.get("days_until_expiration"))
    face_value = normalize_money(row.get("face_value"))
    used_amount = normalize_money(row.get("used_amount"))
    remaining = max(face_value - used_amount, 0)
    progress = int(min(max((used_amount / face_value) * 100 if face_value else 0, 0), 100))

    if upcoming:
        label = "Upcoming"
    elif status == "Used":
        label = "Completed"
    elif status == "Ignored":
        label = "Hidden"
    elif bool(row.get("is_expiring_soon", False)):
        label = "Expiring soon"
    elif status == "Partially Used":
        label = "Partially used"
    else:
        label = "Available"

    return f"**{visual} {name}**  \n:gray[{label} \u00b7 {format_amount(remaining)} left \u00b7 {due_text} \u00b7 {progress}% used]"


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


GENERATED_USAGE_NOTES = {
    "Logged from benefit status update",
    "Backfilled from current benefit status",
    "Logged from Edit Benefits save",
}


def usage_record_from_benefit(
    benefit: pd.Series,
    amount_used: float,
    fully_used: bool,
    note: str,
) -> dict[str, object]:
    return {
        "usage_id": f"usage_{uuid4().hex[:10]}",
        "used_date": pd.Timestamp.today().date().isoformat(),
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


def append_usage_record(benefit: pd.Series, amount_used: float, fully_used: bool, note: str = "Logged from benefit status update") -> None:
    if amount_used <= 0:
        return

    usage = read_usage()
    record = pd.DataFrame(
        [usage_record_from_benefit(benefit, amount_used, fully_used, note)],
        columns=USAGE_COLUMNS,
    )
    save_usage(pd.concat([usage, record], ignore_index=True))


def generated_usage_mask(usage: pd.DataFrame, benefit_id: str, cycle_period: str) -> pd.Series:
    same_benefit_cycle = (
        (usage["benefit_id"].fillna("").astype(str) == benefit_id)
        & (usage["cycle_period"].fillna("").astype(str) == cycle_period)
    )
    generated_notes = usage["notes"].fillna("").astype(str).str.strip().isin(GENERATED_USAGE_NOTES)
    return same_benefit_cycle & generated_notes


def reconcile_generated_usage_record(
    benefit: pd.Series,
    target_used_amount: float,
    fully_used: bool,
    note: str = "Logged from benefit status update",
) -> None:
    benefit_id = clean_display(benefit.get("benefit_id"), "")
    if not benefit_id:
        return

    usage = read_usage()
    cycle_period = clean_display(benefit.get("current_cycle"), "")
    same_benefit_cycle = (
        (usage["benefit_id"].fillna("").astype(str) == benefit_id)
        & (usage["cycle_period"].fillna("").astype(str) == cycle_period)
    )
    generated_mask = generated_usage_mask(usage, benefit_id, cycle_period)
    manual_logged = (
        usage.loc[same_benefit_cycle & ~generated_mask, "used_amount"].apply(normalize_money).sum()
        if not usage.empty
        else 0.0
    )
    generated_target = max(float(target_used_amount) - float(manual_logged), 0.0)

    if not bool(generated_mask.any()) and generated_target <= 0.01:
        return

    next_usage = usage.loc[~generated_mask].copy()
    if generated_target > 0.01:
        record = pd.DataFrame(
            [usage_record_from_benefit(benefit, generated_target, fully_used, note)],
            columns=USAGE_COLUMNS,
        )
        next_usage = pd.concat([next_usage, record], ignore_index=True)
    save_usage(next_usage)


def sync_usage_log_from_benefits() -> int:
    benefits = read_benefits()
    usage = read_usage()
    new_records = []

    for _, benefit in benefits.iterrows():
        used_amount = normalize_money(benefit.get("used_amount"))
        if used_amount <= 0:
            continue

        benefit_id = clean_display(benefit.get("benefit_id"), "")
        cycle_period = clean_display(benefit.get("current_cycle"), "")
        existing = usage[
            (usage["benefit_id"].fillna("").astype(str) == benefit_id)
            & (usage["cycle_period"].fillna("").astype(str) == cycle_period)
        ]
        logged_amount = existing["used_amount"].apply(normalize_money).sum() if not existing.empty else 0.0
        missing_amount = used_amount - logged_amount
        if missing_amount <= 0.01:
            continue

        fully_used = clean_display(benefit.get("status"), "Not Used") == "Used"
        new_records.append(
            usage_record_from_benefit(
                benefit,
                missing_amount,
                fully_used,
                "Backfilled from current benefit status",
            )
        )

    if new_records:
        save_usage(pd.concat([usage, pd.DataFrame(new_records, columns=USAGE_COLUMNS)], ignore_index=True))
    return len(new_records)


def update_benefit_status(benefit_id: str, status: str, used_amount: float | None = None) -> None:
    benefits = read_benefits()
    match = benefits["benefit_id"].astype(str) == str(benefit_id)
    if not match.any():
        st.error("Could not find that benefit in the local CSV.")
        return

    existing = benefits.loc[match].iloc[0].copy()
    face_value = normalize_money(existing.get("face_value"))
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

    updated_benefits = benefits.copy()
    updated_benefits.loc[match, "status"] = status
    updated_benefits.loc[match, "used_amount"] = used_amount
    updated_benefits.loc[match, "remaining_amount"] = remaining_amount
    updated_benefits.loc[match, "usage_percent"] = usage_percent
    updated_benefit = updated_benefits.loc[match].iloc[0].copy()

    benefits_saved = False
    try:
        save_benefits(updated_benefits)
        benefits_saved = True
        reconcile_generated_usage_record(
            updated_benefit,
            used_amount,
            status == "Used",
        )
    except Exception as exc:
        if benefits_saved:
            try:
                save_benefits(benefits)
            except Exception:
                pass
        st.error("Could not finish updating this benefit.")
        st.caption(str(exc))
        return

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


def render_liquid_progress(value: float, text: str) -> None:
    clamped = min(max(float(value), 0), 1)
    percent = clamped * 100
    st.markdown(
        f"""
        <div class="liquid-progress-label">{escape(text)}</div>
        <div class="liquid-progress" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="{percent:.0f}">
            <div class="liquid-progress-fill" style="width:{percent:.2f}%;"></div>
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
    benefit_type = clean_display(row.get("benefit_type"), "Benefit")
    current_cycle = clean_display(row.get("current_cycle"), "")
    status_html = status_badge(status, expiring)
    visual = benefit_visual_cue(row)
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
                cue_col, title_col, action_col = st.columns([0.85, 3.55, 1.55], vertical_alignment="top")
                with cue_col:
                    render_card_cue(row)
            else:
                title_col, action_col = st.columns([4.35, 1.55], vertical_alignment="top")
            expander_host = title_col
            with action_col:
                if st.button("Mark Used", key=f"{key_prefix}_{benefit_id}_quick_used", type="primary", use_container_width=True):
                    update_benefit_status(benefit_id, "Used")
                if st.button("Hide", key=f"{key_prefix}_{benefit_id}_quick_ignore", use_container_width=True):
                    update_benefit_status(benefit_id, "Ignored")
        else:
            title_col, used_col, spacer_col, ignore_col = st.columns([6.2, 1.25, 0.16, 1], vertical_alignment="top")
            expander_host = title_col
            if used_col.button("Mark Used", key=f"{key_prefix}_{benefit_id}_quick_used", type="primary", use_container_width=True):
                update_benefit_status(benefit_id, "Used")
            if ignore_col.button("Hide", key=f"{key_prefix}_{benefit_id}_quick_ignore", use_container_width=True):
                update_benefit_status(benefit_id, "Ignored")

    with expander_host.expander(benefit_summary_label(row), expanded=False):
        st.markdown(
            f"""
            <div class="benefit-tile {'upcoming' if upcoming else ''}">
              <div class="benefit-topline">
                <div class="benefit-title-row">
                  <span class="benefit-visual-cue" aria-hidden="true">{escape(visual)}</span>
                  <div>
                    <div class="benefit-title">{escape(clean_display(row.get("benefit_name")))}</div>
                    <div class="benefit-secondary">
                      {escape(benefit_type)} \u00b7 {format_amount(face_value)} value{f" \u00b7 {escape(current_cycle)}" if current_cycle else ""}
                    </div>
                    <div class="benefit-meta">
                      {status_html}
                      {category_badge(category)}
                      {muted_chip(frequency)}
                      <span class="chip chip-muted">{format_amount(remaining_amount)} left</span>
                    </div>
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
            st.success("Completed benefit shown because archived items are visible.")
            st.caption("This benefit is read-only while completed. Reopen it only if you need to track it again.")
            if st.button("Reopen as not used", key=f"{key_prefix}_{benefit_id}_restore", use_container_width=True):
                update_benefit_status(benefit_id, "Not Used")
        elif status == "Ignored":
            st.warning("Hidden benefit shown because archived items are visible.")
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
                    {format_amount(amount)} used \u00b7 {format_amount(preview_remaining)} left \u00b7 {preview_progress}% used \u00b7 saves as {escape(preview_status)}
                </div>
                """,
                unsafe_allow_html=True,
            )

            action_cols = st.columns([1, 1, 1, 1])
            if action_cols[0].button("Save Amount", key=f"{key_prefix}_{benefit_id}_slider_save", type="primary", use_container_width=True):
                update_benefit_status(benefit_id, preview_status, amount)
            if action_cols[1].button("Mark Used", key=f"{key_prefix}_{benefit_id}_used", use_container_width=True):
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
        try:
            DATA_DIR.mkdir(exist_ok=True)
            ORIGINAL_EXCEL.write_bytes(uploaded.getbuffer())
            result = import_excel_to_csv(ORIGINAL_EXCEL)
        except Exception as exc:
            st.error("Could not import that Excel file.")
            st.caption(str(exc))
            return
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


def show_dashboard(benefits: pd.DataFrame, cards: pd.DataFrame, usage: pd.DataFrame) -> None:
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
    annual_fee_cards = cards.copy()
    if "status" in annual_fee_cards:
        annual_fee_cards = annual_fee_cards[annual_fee_cards["status"].fillna("").astype(str).str.lower() != "closed"]
    total_annual_fee = annual_fee_cards["annual_fee"].apply(normalize_money).sum() if "annual_fee" in annual_fee_cards else 0

    if is_mobile_request():
        force_mobile_dashboard_css()
        with st.container(key="mobile_dashboard"):
            show_mobile_checklist(flagged, active, expiring, used, remaining_value, cards, usage)
        return

    with st.container(key="desktop_dashboard"):
        render_dashboard_kpis(len(active), len(expiring), len(used), remaining_value, total_annual_fee)
        st.markdown('<div class="desktop-stack-spacer"></div>', unsafe_allow_html=True)

        # Desktop layout refinement: split primary navigation from archive scope controls.
        with st.container(key="dashboard_controls"):
            nav_col, archive_col = st.columns([2.75, 1.45], vertical_alignment="bottom")
            with nav_col:
                dashboard_view = st.radio(
                    "View",
                    ["Home", "Cards", "History", "Categories", "Archived"],
                    horizontal=True,
                    key="dashboard_view",
                )
            with archive_col:
                show_hidden = st.toggle(
                    "Show archived benefits",
                    value=False,
                    key="show_archived_benefits",
                )

        browse_data = flagged if show_hidden else active

        if dashboard_view == "Home":
            show_home_view(active, expiring, needs_action)
        elif dashboard_view == "Cards":
            show_by_card_view(browse_data, cards, flagged)
        elif dashboard_view == "History":
            show_usage_history_view(flagged, usage)
        elif dashboard_view == "Categories":
            show_by_category_view(browse_data)
        else:
            show_completed_hidden_view(hidden)


def mobile_status_label(row: pd.Series) -> str:
    status = clean_display(row.get("status"), "Not Used")
    if status == "Used":
        return "Used"
    if status == "Ignored":
        return "Hidden"
    if bool(row.get("is_upcoming", False)):
        return "Upcoming"
    if bool(row.get("is_expiring_soon", False)):
        return "Expiring Soon"
    if status == "Partially Used":
        return "Partially Used"
    return "Available"


def mobile_status_class(label: str) -> str:
    return label.lower().replace(" ", "-")


def mobile_benefit_summary_label(row: pd.Series) -> str:
    name = clean_display(row.get("benefit_name"), "Unnamed benefit")
    visual = benefit_visual_cue(row)
    label = mobile_status_label(row)
    upcoming = bool(row.get("is_upcoming", False))
    start_label = date_label(row.get("cycle_start_date"))
    due_text = f"Starts {start_label}" if upcoming and start_label else due_text_from_days(row.get("days_until_expiration"))
    face_value = normalize_money(row.get("face_value"))
    used_amount = normalize_money(row.get("used_amount"))
    remaining = max(face_value - used_amount, 0)
    progress = int(min(max((used_amount / face_value) * 100 if face_value else 0, 0), 100))
    progress_text = f"{progress}% used" if face_value else "No progress"
    return f"**{visual} {name}**  \n:gray[{label} - {due_text} - {format_amount(remaining)} left - {progress_text}]"


def render_mobile_benefit_card(row: pd.Series, key_prefix: str) -> None:
    benefit_id = clean_display(row.get("benefit_id"), "")
    benefit_name = clean_display(row.get("benefit_name"), "Unnamed benefit")
    card_name = clean_display(row.get("card_name"), "Card not set")
    owner = clean_display(row.get("owner"), "")
    status = clean_display(row.get("status"), "Not Used")
    upcoming = bool(row.get("is_upcoming", False))
    start_label = date_label(row.get("cycle_start_date"))
    due_text = f"Starts {start_label}" if upcoming and start_label else due_text_from_days(row.get("days_until_expiration"))
    due_date = date_label(row.get("expiration_date")) or "No date"
    face_value = normalize_money(row.get("face_value"))
    used_amount = normalize_money(row.get("used_amount"))
    remaining = max(face_value - used_amount, 0)
    realistic_value = normalize_money(row.get("realistic_value"))
    progress = int(min(max((used_amount / face_value) * 100 if face_value else 0, 0), 100))
    label = mobile_status_label(row)
    category = clean_display(row.get("category"), "Other")
    benefit_type = clean_display(row.get("benefit_type"), "Benefit")
    frequency = clean_display(row.get("frequency"), "")
    current_cycle = clean_display(row.get("current_cycle"), "")
    notes = clean_display(row.get("notes"), "")
    source = clean_display(row.get("source_url"), "")
    visual = benefit_visual_cue(row)
    safe_id = benefit_id or f"benefit_{key_prefix}"
    container_key = f"mobile_card_{key_prefix}_{safe_id}".replace(" ", "_").replace("-", "_")

    with st.expander(mobile_benefit_summary_label(row), expanded=False):
        st.markdown(
            f"""
            <div class="mobile-benefit-card">
                <div class="mobile-benefit-main">
                    <div class="mobile-benefit-title-row">
                        <span class="mobile-benefit-visual" aria-hidden="true">{escape(visual)}</span>
                        <div>
                            <div class="mobile-benefit-name">{escape(benefit_name)}</div>
                            <div class="mobile-benefit-card-name">{escape(card_name)}</div>
                            {f'<div class="mobile-benefit-owner">{escape(owner)}</div>' if owner else ''}
                        </div>
                    </div>
                    <span class="mobile-status mobile-status-{mobile_status_class(label)}">{escape(label)}</span>
                </div>
                <div class="mobile-benefit-facts">
                    <div>
                        <span>Due</span>
                        <strong>{escape(due_text)}</strong>
                        <small>{escape(due_date)}</small>
                    </div>
                    <div>
                        <span>Remaining</span>
                        <strong>{format_amount(remaining)}</strong>
                        <small>{progress}% used</small>
                    </div>
                    <div>
                        <span>Used</span>
                        <strong>{format_amount(used_amount)}</strong>
                        <small>{escape(status)}</small>
                    </div>
                    <div>
                        <span>Total</span>
                        <strong>{format_amount(face_value)}</strong>
                        <small>{format_amount(realistic_value)} realistic</small>
                    </div>
                    <div>
                        <span>Type</span>
                        <strong>{escape(benefit_type)}</strong>
                        <small>{escape(category)}</small>
                    </div>
                    <div>
                        <span>Cycle</span>
                        <strong>{escape(current_cycle or "Not set")}</strong>
                        <small>{escape(frequency or "Frequency not set")}</small>
                    </div>
                </div>
                <div class="mobile-progress-shell" aria-hidden="true">
                    <div class="mobile-progress-fill" style="width:{progress}%;"></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if notes:
            st.markdown(
                f"""
                <div class="mobile-detail-note">
                    <span>Details / how to use</span>
                    <p>{escape(notes)}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        if source:
            st.link_button("Source", source, use_container_width=True)

        if status == "Used":
            st.success("Completed benefit. Reopen it only if you need to track it again.")
            if st.button("Reopen", key=f"{container_key}_reopen", use_container_width=True):
                update_benefit_status(benefit_id, "Not Used")
        elif status == "Ignored":
            st.warning("Hidden benefit. Reopen it if it becomes relevant again.")
            if st.button("Reopen", key=f"{container_key}_restore", use_container_width=True):
                update_benefit_status(benefit_id, "Not Used")
        elif upcoming:
            st.info("This benefit has not reached its start window yet. Usage actions will unlock when the cycle starts.")
            st.button("Not active yet", key=f"{container_key}_upcoming", use_container_width=True, disabled=True)
        else:
            slider_reset_key = f"{container_key}_slider_reset_token"
            slider_token = st.session_state.get(slider_reset_key, 0)
            slider_key = f"{container_key}_mobile_amount_{slider_token}"
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
                <div class="mobile-adjust-summary">
                    {format_amount(amount)} used - {format_amount(preview_remaining)} left - {preview_progress}% used - saves as {escape(preview_status)}
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.container(key=f"{container_key}_actions"):
                save_col, used_col = st.columns(2)
                reset_col, ignore_col = st.columns(2)
                if save_col.button("Save Amount", key=f"{container_key}_mobile_save_amount", type="primary", use_container_width=True):
                    update_benefit_status(benefit_id, preview_status, amount)
                if used_col.button("Mark Used", key=f"{container_key}_used", use_container_width=True):
                    update_benefit_status(benefit_id, "Used")
                if reset_col.button("Reset", key=f"{container_key}_reset", use_container_width=True):
                    st.session_state[slider_reset_key] = slider_token + 1
                    update_benefit_status(benefit_id, "Not Used")
                if ignore_col.button("Hide", key=f"{container_key}_ignore", use_container_width=True):
                    update_benefit_status(benefit_id, "Ignored")


def mobile_card_group_art(row: pd.Series) -> str:
    image_path = find_card_image(row)
    card_name = clean_display(row.get("card_name"), "Card")
    if image_path:
        return f'<img class="mobile-card-group-image" src="{card_image_data_uri(image_path)}" alt="{escape(card_name)}">'

    start, end, text_color, brand, _ = card_art_style(row.get("card_name"), row.get("issuer"))
    return f"""
    <div class="mobile-card-group-fallback" style="background: linear-gradient(135deg, {start}, {end}); color: {text_color};">
        <span>{escape(brand)}</span>
    </div>
    """


def mobile_card_group_label_art(row: pd.Series) -> str:
    card_name = clean_display(row.get("card_name"), "Card")
    image_path = find_card_image(row)
    if image_path:
        return f"![{card_name}]({card_image_data_uri(image_path)})"

    start, end, text_color, brand, _ = card_art_style(row.get("card_name"), row.get("issuer"))
    svg = f"""
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 72 45">
      <defs>
        <linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stop-color="{start}"/>
          <stop offset="1" stop-color="{end}"/>
        </linearGradient>
      </defs>
      <rect width="72" height="45" rx="7" fill="url(#g)"/>
      <rect x="8" y="11" width="16" height="10" rx="2" fill="rgba(255,255,255,.38)"/>
      <text x="8" y="35" fill="{text_color}" font-family="Arial, sans-serif" font-size="8" font-weight="700">{escape(brand[:10])}</text>
    </svg>
    """
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"![{card_name}](data:image/svg+xml;base64,{encoded})"


def render_mobile_card_group(card_label: str, group: pd.DataFrame, key_prefix: str) -> None:
    expiring_count = int(group["is_expiring_soon"].sum()) if "is_expiring_soon" in group else 0
    active_now = group[(~group["status"].isin(["Used", "Ignored"])) & (~group["is_upcoming"])]
    upcoming = group[group["is_upcoming"]]
    archived = group[group["status"].isin(["Used", "Ignored"])]
    available_count = len(active_now)
    upcoming_count = len(upcoming)
    remaining_value = group["remaining_amount"].apply(normalize_money).sum()
    owner = clean_display(group["owner"].dropna().iloc[0], "") if "owner" in group and not group["owner"].dropna().empty else ""
    first_row = group.iloc[0]
    owner_label = f" - {owner}" if owner else ""
    expander_label = (
        f"{mobile_card_group_label_art(first_row)} **{card_label}**{owner_label}  \n"
        f":gray[**{available_count} active** - **{upcoming_count} upcoming** - **{format_amount(remaining_value)} left**]"
    )

    with st.expander(expander_label, expanded=False):
        st.markdown(
            f"""
            <div class="mobile-card-group-header">
                {mobile_card_group_art(first_row)}
                <div>
                    <div class="mobile-card-group-title">{escape(card_label)}</div>
                    {f'<div class="mobile-card-group-owner">{escape(owner)}</div>' if owner else ''}
                </div>
                <div class="mobile-card-group-stats">
                    <span>{available_count} active</span>
                    <span>{upcoming_count} upcoming</span>
                    <span>{expiring_count} soon</span>
                    <strong>{format_amount(remaining_value)}</strong>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if not active_now.empty:
            render_mobile_section("Available now", active_now, f"{key_prefix}_active")
        if not upcoming.empty:
            render_mobile_section("Upcoming", upcoming, f"{key_prefix}_upcoming")
        if not archived.empty:
            render_mobile_section("Completed / Hidden", archived, f"{key_prefix}_archived")


def render_mobile_section(title: str, benefits: pd.DataFrame, key_prefix: str, limit: int | None = None) -> None:
    visual = section_visual_cue(title)
    st.markdown(
        f'<div class="mobile-section-heading"><span class="mobile-section-emoji" aria-hidden="true">{escape(visual)}</span>{escape(title)}</div>',
        unsafe_allow_html=True,
    )
    if benefits.empty:
        st.markdown('<div class="mobile-empty-state">Nothing here right now.</div>', unsafe_allow_html=True)
        return

    visible = sort_mobile_benefits(benefits)
    if limit is not None:
        visible = visible.head(limit)
    for index, (_, benefit) in enumerate(visible.iterrows()):
        render_mobile_benefit_card(benefit, f"{key_prefix}_{index}")


def render_mobile_annual_fee_card(row: pd.Series, key_prefix: str) -> None:
    card_name = clean_display(row.get("card_name"), "Card not set")
    owner = clean_display(row.get("owner"), "")
    annual_fee = normalize_money(row.get("annual_fee"))
    fee_date = date_label(row.get("annual_fee_date")) or "No date"
    days_left = int(normalize_money(row.get("days_left")))
    due_text = "Due today" if days_left == 0 else f"Due in {days_left} days"
    label = "Due today" if days_left == 0 else "Fee soon"

    with st.container(key=f"mobile_fee_{key_prefix}".replace(" ", "_").replace("-", "_")):
        st.markdown(
            f"""
            <div class="mobile-benefit-card">
                <div class="mobile-benefit-main">
                    <div class="mobile-benefit-title-row">
                        <span class="mobile-benefit-visual" aria-hidden="true">💳</span>
                        <div>
                            <div class="mobile-benefit-name">{escape(card_name)}</div>
                            <div class="mobile-benefit-card-name">Annual fee reminder</div>
                            {f'<div class="mobile-benefit-owner">{escape(owner)}</div>' if owner else ''}
                        </div>
                    </div>
                    <span class="mobile-status mobile-status-expiring-soon">{escape(label)}</span>
                </div>
                <div class="mobile-benefit-facts">
                    <div>
                        <span>Due</span>
                        <strong>{escape(due_text)}</strong>
                        <small>{escape(fee_date)}</small>
                    </div>
                    <div>
                        <span>Annual fee</span>
                        <strong>{format_amount(annual_fee)}</strong>
                        <small>Review card value</small>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_mobile_annual_fees(fee_reminders: pd.DataFrame, limit: int | None = None) -> None:
    st.markdown(
        '<div class="mobile-section-heading"><span class="mobile-section-emoji" aria-hidden="true">💳</span>Annual Fees</div>',
        unsafe_allow_html=True,
    )
    if fee_reminders.empty:
        st.markdown('<div class="mobile-empty-state">No annual fees due soon.</div>', unsafe_allow_html=True)
        return

    visible = fee_reminders.head(limit) if limit is not None else fee_reminders
    for index, (_, fee) in enumerate(visible.iterrows()):
        render_mobile_annual_fee_card(fee, f"annual_fee_{index}")


def render_mobile_category_groups(benefits: pd.DataFrame) -> None:
    if benefits.empty:
        st.markdown('<div class="mobile-empty-state">No active benefits to show.</div>', unsafe_allow_html=True)
        return

    category_order = ["Dining", "Rideshare", "Travel", "Hotel", "Airline", "Shopping", "Entertainment", "Other"]
    categories = sorted([category for category in benefits["category"].dropna().unique() if normalize_text(category)])
    ordered = [category for category in category_order if category in categories]
    ordered.extend([category for category in categories if category not in ordered])

    for index, category in enumerate(ordered):
        group = benefits[benefits["category"] == category]
        if group.empty:
            continue
        active_count = int(((~group["status"].isin(["Used", "Ignored"])) & (~group["is_upcoming"])).sum())
        upcoming_count = int(group["is_upcoming"].sum())
        remaining = group["remaining_amount"].apply(normalize_money).sum()
        visual = category_icon(category)
        label = (
            f"**{visual} {category}**  \n"
            f":gray[**{active_count} active** - **{upcoming_count} upcoming** - **{format_amount(remaining)} left**]"
        )
        with st.expander(label, expanded=False):
            render_mobile_section(category, group, f"mobile_category_{index}")


def render_mobile_wallet_hero(
    active_now_count: int,
    upcoming_count: int,
    archived_count: int,
    due_soon_count: int,
    monthly_count: int,
    remaining_value: float,
    cards: pd.DataFrame,
) -> None:
    open_cards = cards.copy()
    if "status" in open_cards:
        open_cards = open_cards[open_cards["status"].fillna("").astype(str).str.lower() != "closed"]
    st.markdown(
        f"""
        <div class="mobile-wallet-hero">
            <div class="mobile-wallet-topline">
                <span>Benefit Wallet</span>
                <span>{len(open_cards)} cards</span>
            </div>
            <div class="mobile-wallet-balance-label">Remaining value</div>
            <div class="mobile-wallet-balance">{format_amount(remaining_value)}</div>
            <div class="mobile-wallet-chip-row">
                <span>{due_soon_count} due soon</span>
                <span>{monthly_count} this month</span>
                <span>{upcoming_count} upcoming</span>
            </div>
            <div class="mobile-wallet-stats" aria-label="Benefit summary">
                <div><span>Active</span><strong>{active_now_count}</strong></div>
                <div><span>Upcoming</span><strong>{upcoming_count}</strong></div>
                <div><span>Archived</span><strong>{archived_count}</strong></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_mobile_checklist(
    flagged: pd.DataFrame,
    active: pd.DataFrame,
    expiring: pd.DataFrame,
    used: pd.DataFrame,
    remaining_value: float,
    cards: pd.DataFrame,
    usage: pd.DataFrame,
) -> None:
    due_soon = mobile_attention_benefits(active)
    this_month = mobile_monthly_not_used(active)
    active_now = active[~active["is_upcoming"]].copy()
    upcoming = active[active["is_upcoming"]].copy()
    partial = active_now[active_now["status"] == "Partially Used"].copy()
    completed = flagged[flagged["status"] == "Used"].copy()
    ignored = flagged[flagged["status"] == "Ignored"].copy()
    archived = flagged[flagged["status"].isin(["Used", "Ignored"])].copy()
    fee_reminders = annual_fee_reminders(cards)

    with st.container(key="mobile_theme_switch"):
        render_theme_selector("mobile_theme_label", horizontal=True, label="Theme")

    render_mobile_wallet_hero(
        len(active_now),
        len(upcoming),
        len(archived),
        len(due_soon),
        len(this_month),
        remaining_value,
        cards,
    )

    selected_view = st.radio(
        "Today's reminders",
        [
            "Home",
            "Cards",
            "History",
            "Categories",
            "Archived",
        ],
        horizontal=True,
        label_visibility="collapsed",
        key="mobile_benefit_view",
    )

    if selected_view == "Home":
        render_mobile_section("Priority Reminders", due_soon, "mobile_home_due", limit=6)
        render_mobile_section("Not Used This Month", this_month, "mobile_home_month", limit=6)
        render_mobile_section("Partially Used", partial, "mobile_home_partial", limit=4)
        render_mobile_section("Upcoming Next", upcoming, "mobile_home_upcoming", limit=4)
        render_mobile_annual_fees(fee_reminders, limit=4)
        if due_soon.empty and this_month.empty and partial.empty and upcoming.empty and fee_reminders.empty:
            st.success("No urgent benefit actions right now.")
        return

    if selected_view == "Categories":
        render_mobile_category_groups(active)
        return

    if selected_view == "History":
        st.markdown(
            '<div class="mobile-section-heading"><span class="mobile-section-emoji" aria-hidden="true">🗓️</span>Usage History</div>',
            unsafe_allow_html=True,
        )
        show_usage_history_view(flagged, usage, mobile=True)
        return

    if selected_view == "Archived":
        completed_tab, hidden_tab = st.tabs([f"Completed ({len(completed)})", f"Hidden ({len(ignored)})"])
        with completed_tab:
            render_mobile_section("Completed", completed, "mobile_completed")
        with hidden_tab:
            render_mobile_section("Hidden", ignored, "mobile_hidden")
        return

    selected = active.sort_values(["is_upcoming", "expiration_date", "benefit_name"])
    if selected.empty:
        st.markdown('<div class="mobile-empty-state">No card benefits to show.</div>', unsafe_allow_html=True)
        return

    selected = selected.copy()
    selected["_card_group_owner"] = selected["owner"].map(lambda value: clean_display(value, ""))
    selected["_card_group_name"] = selected["card_name"].map(lambda value: clean_display(value, "No card set"))
    grouped = selected.groupby(["_card_group_owner", "_card_group_name"], sort=False)
    for group_index, ((_, card_label), group) in enumerate(grouped):
        render_mobile_card_group(card_label, group, f"checklist_card_{group_index}")


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
        st.markdown('<div class="empty-chip">Nothing here.</div>', unsafe_allow_html=True)
        return
    for index, (_, benefit) in enumerate(benefits.iterrows()):
        render_benefit_tile(
            benefit,
            f"{key_prefix}_{index}",
            quick_actions_layout="vertical",
            show_card_cue=True,
        )


def show_by_card_view(
    flagged: pd.DataFrame,
    cards: pd.DataFrame | None = None,
    all_benefits: pd.DataFrame | None = None,
) -> None:
    if flagged.empty:
        st.info("No active benefits to show. Use the toggle above or open Archived.")
        return
    if cards is None:
        cards = read_cards()
    if all_benefits is None:
        all_benefits = benefit_status_flags(read_benefits())

    if cards.empty:
        cards = flagged[["owner", "card_name"]].drop_duplicates().copy()
        cards["issuer"] = ""
        cards["card_id"] = ""

    owners = ["All owners"] + sorted([owner for owner in flagged["owner"].dropna().unique() if normalize_text(owner)])
    with st.container(key="card_view_filters"):
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

        card_key = (
            normalize_text(card.get("card_id"))
            or f"{normalize_text(card.get('owner'))}_{normalize_text(card.get('card_name'))}".replace(" ", "_")
        )
        with st.container(border=True, key=f"card_section_{card_key}"):
            left, right = st.columns([0.78, 2.85], vertical_alignment="top")
            with left:
                render_card_art(card, len(card_benefits))
                done_count = int(all_card_benefits["status"].isin(["Used", "Ignored"]).sum())
                total_count = max(len(all_card_benefits), 1)
                render_liquid_progress(done_count / total_count, f"{done_count}/{total_count} complete or hidden")
            with right:
                expiring_count = int(card_benefits["is_expiring_soon"].sum())
                tracked_card_benefits = all_card_benefits[all_card_benefits["status"] != "Ignored"]
                active_count = int(tracked_card_benefits["is_active"].sum()) if "is_active" in tracked_card_benefits else len(card_benefits)
                remaining_value = tracked_card_benefits["remaining_amount"].apply(normalize_money).sum()
                used_value = tracked_card_benefits["used_amount"].apply(normalize_money).sum()
                total_value = tracked_card_benefits["face_value"].apply(normalize_money).sum()
                value_progress = used_value / total_value if total_value else 0
                issuer = clean_display(card.get("issuer"), "Issuer unknown")
                version = clean_display(card.get("card_version"), "")
                network_label = f"{issuer} \u00b7 {version}" if version else issuer
                owner = clean_display(card.get("owner"), "Unassigned")
                st.markdown(
                    f"""
                    <div class="card-section-header">
                        <div>
                            <div class="card-section-owner">{escape(owner)}</div>
                            <h3>{escape(clean_display(card.get("card_name")))}</h3>
                            <p>{escape(network_label)} \u00b7 {escape(next_membership_fee_label(card))}</p>
                        </div>
                        <div class="card-section-status">
                            <span>{expiring_count} expiring soon</span>
                        </div>
                    </div>
                    <div class="card-stat-grid">
                        <div><span>Active</span><strong>{active_count}</strong></div>
                        <div class="emphasis"><span>Remaining</span><strong>{format_amount(remaining_value)}</strong></div>
                        <div><span>Used value</span><strong>{format_amount(used_value)}</strong></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                render_liquid_progress(value_progress, f"{int(value_progress * 100)}% of tracked value used")
                with st.expander("Show benefits", expanded=expiring_count > 0):
                    for _, benefit in card_benefits.sort_values(["status", "expiration_date", "benefit_name"]).iterrows():
                        render_benefit_tile(benefit, f"card_{normalize_text(card.get('card_id')) or normalize_text(card.get('card_name'))}")


def show_by_category_view(flagged: pd.DataFrame) -> None:
    st.caption("Scan across cards by benefit category.")
    if flagged.empty:
        st.info("No active benefits to show. Use the toggle above or open Archived.")
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
                    st.caption(f"{clean_display(benefit.get('owner'))} \u00b7 {clean_display(benefit.get('card_name'))}")
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
    st.caption("Completed and hidden benefits stay recoverable here.")
    if hidden.empty:
        st.info("No completed or hidden benefits yet.")
        return

    completed = hidden[hidden["status"] == "Used"]
    ignored = hidden[hidden["status"] == "Ignored"]
    completed_tab, ignored_tab = st.tabs([f"Completed ({len(completed)})", f"Hidden ({len(ignored)})"])
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
    st.set_page_config(
        page_title="Credit Card Benefit Tracker",
        page_icon=app_icon_page_config_value(),
        layout="wide",
        initial_sidebar_state="expanded",
    )
    inject_app_icon_metadata()
    theme = active_app_theme()
    inject_styles()
    inject_theme_styles(theme)

    try:
        ensure_data_files()
    except Exception as exc:
        st.error("Could not initialize the data backend.")
        st.caption(str(exc))
        st.stop()

    st.markdown(
        """
        <div class="page-title-block">
            <h1>Credit Card Benefit Tracker</h1>
            <p>See which card benefits to use next, what is expiring soon, and how much value is still available.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if not is_mobile_request():
        with st.container(key="desktop_theme_switch"):
            render_theme_selector("desktop_theme_label", horizontal=True, label="Theme")

    try:
        cards = read_cards()
        benefits = read_benefits()
        usage = read_usage()
    except Exception as exc:
        st.error("Could not load tracker data.")
        st.caption(str(exc))
        st.stop()

    with st.sidebar:
        # Desktop sidebar polish: separate app navigation from secondary local data counts.
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-eyebrow">Local tracker</div>
                <div class="sidebar-title">Benefit desk</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        section = st.radio(
            "App",
            ["Dashboard", "Raw Data"],
        )
        st.markdown(
            f"""
            <div class="sidebar-data-summary">
                <div class="sidebar-section-label">Data summary</div>
                <div><span>Cards</span><strong>{len(cards)}</strong></div>
                <div><span>Benefits</span><strong>{len(benefits)}</strong></div>
                <div><span>Usage records</span><strong>{len(usage)}</strong></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if benefits.empty:
        show_importer()
        st.divider()

    if section == "Dashboard":
        show_dashboard(benefits, cards, usage)
    else:
        show_raw_data(cards, benefits, usage)


if __name__ == "__main__":
    main()

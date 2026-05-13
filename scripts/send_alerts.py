from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd


APP_DIR = Path(__file__).resolve().parents[1]
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from alerts import EmailConfig, build_alert_preview, log_rows_for_alerts, render_email_html, send_html_email, subject_for_preview
from storage import get_storage


DATA_DIR = APP_DIR / "data"


def streamlit_secret(name: str) -> Any:
    try:
        import streamlit as st

        return st.secrets.get(name, "")
    except Exception:
        return ""


def config_value(name: str, default: str = "") -> str:
    value = streamlit_secret(name)
    if value:
        return str(value).strip()
    return os.environ.get(name, default).strip()


def config_bool(name: str, default: bool = False) -> bool:
    value = config_value(name)
    if not value:
        return default
    return value.lower() in {"1", "true", "yes", "y", "on"}


def email_config_from_settings() -> EmailConfig:
    port = config_value("ALERT_SMTP_PORT", "587")
    try:
        smtp_port = int(port)
    except ValueError:
        raise ValueError("ALERT_SMTP_PORT must be a number.") from None

    username = config_value("ALERT_SMTP_USERNAME")
    sender_email = config_value("ALERT_SENDER_EMAIL") or username
    return EmailConfig(
        smtp_host=config_value("ALERT_SMTP_HOST"),
        smtp_port=smtp_port,
        smtp_username=username,
        smtp_password=config_value("ALERT_SMTP_PASSWORD"),
        sender_email=sender_email,
        sender_name=config_value("ALERT_SENDER_NAME") or "Credit Card Benefit Tracker",
        use_tls=config_bool("ALERT_SMTP_USE_TLS", True),
        use_ssl=config_bool("ALERT_SMTP_USE_SSL", False),
    )


def require_email_settings() -> tuple[EmailConfig, str]:
    config = email_config_from_settings()
    recipient_email = config_value("ALERT_RECIPIENT_EMAIL")
    missing = config.missing_fields()
    if not recipient_email:
        missing.append("ALERT_RECIPIENT_EMAIL")
    if missing:
        raise ValueError(f"Missing email configuration: {', '.join(missing)}")
    return config, recipient_email


def parse_run_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise argparse.ArgumentTypeError("Use YYYY-MM-DD format for --date.") from None


def test_email_html(greeting_name: str, app_url: str) -> str:
    cta = ""
    if app_url:
        cta = (
            f'<p><a href="{app_url}" '
            'style="display:inline-block;background:#312e81;color:#ffffff;text-decoration:none;'
            'border-radius:10px;padding:12px 18px;font-size:14px;font-weight:700;">'
            "Open Credit Card Benefit Tracker</a></p>"
        )
    return f"""<!doctype html>
<html>
  <body style="margin:0;padding:0;background:#f5f7fb;font-family:Arial,Helvetica,sans-serif;color:#172033;">
    <div style="max-width:640px;margin:0 auto;padding:28px 12px;">
      <div style="background:#ffffff;border:1px solid #e6e8f3;border-radius:18px;padding:26px;">
        <div style="font-size:24px;line-height:1.2;font-weight:800;color:#172033;">Credit Card Benefit Tracker Test Email</div>
        <p style="font-size:15px;line-height:1.55;color:#334155;">Hi {greeting_name},</p>
        <p style="font-size:15px;line-height:1.55;color:#334155;">This is a test email only. It does not mark any real alert as sent and does not write duplicate-prevention rows to alert_log.</p>
        {cta}
        <div style="border-top:1px solid #e6e8f3;margin-top:24px;padding-top:14px;font-size:12px;line-height:1.5;color:#64748b;">
          Sent by the manual alert runner.
        </div>
      </div>
    </div>
  </body>
</html>"""


def send_test_email() -> int:
    config, recipient_email = require_email_settings()
    greeting_name = config_value("ALERT_GREETING_NAME") or "Xinyi"
    app_url = config_value("ALERT_APP_URL")
    subject = "Test email: Credit Card Benefit Tracker alerts"
    send_html_email(config, recipient_email, subject, test_email_html(greeting_name, app_url))
    print(f"Test email sent to {recipient_email}. alert_log was not modified.")
    return 0


def send_due_alerts(run_date: date, backend: str | None = None) -> int:
    config, recipient_email = require_email_settings()
    storage = get_storage(DATA_DIR, backend=backend)
    benefits = storage.read_benefits()
    cards = storage.read_cards()
    alert_log = storage.read_alert_log()

    preview = build_alert_preview(
        benefits=benefits,
        cards=cards,
        alert_log=alert_log,
        run_date=run_date,
        recipient_email=recipient_email,
    )
    due_count = preview.benefit_count + preview.annual_fee_count
    skipped_count = len(preview.skipped_benefits) + len(preview.skipped_annual_fees)
    print(f"Alert run date: {run_date.isoformat()}")
    print(f"Due alerts: {due_count} ({preview.benefit_count} benefits, {preview.annual_fee_count} annual fees)")
    print(f"Skipped duplicates: {skipped_count}")

    if due_count == 0:
        print("No alerts were due. Email was not sent.")
        return 0

    greeting_name = config_value("ALERT_GREETING_NAME") or "Xinyi"
    app_url = config_value("ALERT_APP_URL")
    subject = subject_for_preview(preview)
    html = render_email_html(preview, greeting_name=greeting_name, app_url=app_url)

    try:
        send_html_email(config, recipient_email, subject, html)
    except Exception as exc:
        failed_rows = log_rows_for_alerts(
            preview.benefits,
            preview.annual_fees,
            recipient_email,
            status="failed",
            error_message=str(exc),
        )
        if not failed_rows.empty:
            storage.save_alert_log(pd.concat([alert_log, failed_rows], ignore_index=True))
        raise

    sent_rows = log_rows_for_alerts(preview.benefits, preview.annual_fees, recipient_email, status="sent")
    if sent_rows.empty:
        print("Email sent, but there were no alert rows to log.")
        return 0

    try:
        storage.save_alert_log(pd.concat([alert_log, sent_rows], ignore_index=True))
    except Exception as exc:
        raise RuntimeError(
            "Email was sent, but writing alert_log failed. Check the alert_log worksheet/table permissions and rerun only after resolving this to avoid duplicate sends."
        ) from exc

    print(f"Email sent to {recipient_email}. Logged {len(sent_rows)} sent alert row(s).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Send due credit card benefit reminder emails.")
    parser.add_argument("--date", type=parse_run_date, default=date.today(), help="Run date in YYYY-MM-DD format.")
    parser.add_argument("--backend", choices=["local", "google_sheets"], help="Override DATA_BACKEND for this run.")
    parser.add_argument("--test-email", action="store_true", help="Send a test email without writing alert_log rows.")
    args = parser.parse_args()

    if args.test_email:
        return send_test_email()
    return send_due_alerts(args.date, backend=args.backend)


if __name__ == "__main__":
    raise SystemExit(main())

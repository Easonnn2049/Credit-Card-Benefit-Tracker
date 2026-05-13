from __future__ import annotations

from datetime import date
from html import escape

import pandas as pd

from .rules import AlertPreview


def _money(value: object) -> float:
    if pd.isna(value) or value == "":
        return 0.0
    if isinstance(value, str):
        value = value.replace("$", "").replace(",", "").strip()
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _format_money(value: object) -> str:
    amount = _money(value)
    return f"${amount:,.0f}" if amount == round(amount) else f"${amount:,.2f}"


def _format_date(value: object) -> str:
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return "Date not set"
    return f"{parsed.strftime('%b')} {parsed.day}, {parsed.year}" if hasattr(parsed, "strftime") else str(value)


def _days_text(days_left: object) -> str:
    try:
        days = int(days_left)
    except (TypeError, ValueError):
        return ""
    if days == 0:
        return "Due today"
    if days == 1:
        return "1 day left"
    return f"{days} days left"


def _most_urgent_date(preview: AlertPreview) -> str:
    dates = []
    if not preview.benefits.empty:
        dates.extend(preview.benefits["due_date"].dropna().astype(str).tolist())
    if not preview.annual_fees.empty:
        dates.extend(preview.annual_fees["annual_fee_date"].dropna().astype(str).tolist())
    if not dates:
        return "No reminders due"
    return _format_date(sorted(dates)[0])


def subject_for_preview(preview: AlertPreview) -> str:
    if preview.benefit_count and not preview.annual_fee_count:
        return f"Credit benefit reminder: {preview.benefit_count} items need attention"
    if preview.annual_fee_count and not preview.benefit_count:
        return "Annual fee reminder: card fee due soon"
    if preview.benefit_count or preview.annual_fee_count:
        return f"Credit card reminders for {preview.run_date.isoformat()}"
    return f"No credit card reminders for {preview.run_date.isoformat()}"


def _benefit_card(row: pd.Series) -> str:
    value = _format_money(row.get("remaining_amount"))
    if _money(row.get("remaining_amount")) <= 0:
        value = _format_money(row.get("face_value"))
    owner = str(row.get("owner", "")).strip()
    card_label = str(row.get("card_name", ""))
    if owner:
        card_label = f"{card_label} - {owner}"

    return f"""
    <tr>
      <td style="padding:0 0 14px 0;">
        <div style="border:1px solid #e6e8f3;border-radius:14px;background:#ffffff;padding:16px;">
          <div style="font-size:13px;color:#64748b;margin-bottom:4px;">{escape(card_label)}</div>
          <div style="font-size:17px;line-height:1.35;font-weight:700;color:#172033;margin-bottom:10px;">{escape(str(row.get("benefit_name", "")))}</div>
          <div style="margin-bottom:12px;">
            <span style="display:inline-block;background:#eef2ff;color:#4f46e5;border-radius:999px;padding:5px 10px;font-size:12px;font-weight:700;">Available</span>
            <span style="display:inline-block;background:#eff6ff;color:#2563eb;border-radius:999px;padding:5px 10px;font-size:12px;font-weight:700;margin-left:6px;">{escape(str(row.get("display_cycle", "Benefit")))}</span>
          </div>
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-collapse:collapse;">
            <tr>
              <td style="font-size:12px;color:#64748b;">Remaining value</td>
              <td style="font-size:12px;color:#64748b;">Due/reset date</td>
              <td style="font-size:12px;color:#64748b;">Timing</td>
            </tr>
            <tr>
              <td style="font-size:16px;font-weight:700;color:#172033;padding-top:3px;">{escape(value)}</td>
              <td style="font-size:16px;font-weight:700;color:#172033;padding-top:3px;">{escape(_format_date(row.get("due_date")))}</td>
              <td style="font-size:16px;font-weight:700;color:#172033;padding-top:3px;">{escape(_days_text(row.get("days_left")))}</td>
            </tr>
          </table>
          <div style="font-size:13px;line-height:1.45;color:#475569;margin-top:12px;">{escape(str(row.get("action_hint", "Use before this cycle resets.")))}</div>
        </div>
      </td>
    </tr>
    """


def _annual_fee_card(row: pd.Series) -> str:
    days_label = _days_text(row.get("days_left"))
    badge_bg = "#fff7ed" if int(row.get("days_left", 1)) != 0 else "#fef2f2"
    badge_color = "#b45309" if int(row.get("days_left", 1)) != 0 else "#b91c1c"
    owner = str(row.get("owner", "")).strip()
    card_label = str(row.get("card_name", ""))
    if owner:
        card_label = f"{card_label} - {owner}"
    return f"""
    <tr>
      <td style="padding:0 0 14px 0;">
        <div style="border:1px solid #f2dec0;border-radius:14px;background:#fffaf0;padding:16px;">
          <div style="font-size:17px;line-height:1.35;font-weight:700;color:#172033;margin-bottom:10px;">{escape(card_label)}</div>
          <div style="margin-bottom:12px;">
            <span style="display:inline-block;background:{badge_bg};color:{badge_color};border-radius:999px;padding:5px 10px;font-size:12px;font-weight:700;">{escape(days_label)}</span>
          </div>
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-collapse:collapse;">
            <tr>
              <td style="font-size:12px;color:#64748b;">Annual fee</td>
              <td style="font-size:12px;color:#64748b;">Fee date</td>
            </tr>
            <tr>
              <td style="font-size:16px;font-weight:700;color:#172033;padding-top:3px;">{escape(_format_money(row.get("annual_fee")))}</td>
              <td style="font-size:16px;font-weight:700;color:#172033;padding-top:3px;">{escape(_format_date(row.get("annual_fee_date")))}</td>
            </tr>
          </table>
          <div style="font-size:13px;line-height:1.45;color:#475569;margin-top:12px;">{escape(str(row.get("action_hint", "")))}</div>
        </div>
      </td>
    </tr>
    """


def _section(title: str, rows_html: str, empty_text: str) -> str:
    body = rows_html or f'<tr><td style="font-size:14px;color:#64748b;padding-bottom:14px;">{escape(empty_text)}</td></tr>'
    return f"""
    <tr>
      <td style="padding-top:22px;">
        <h2 style="margin:0 0 12px 0;font-size:18px;line-height:1.3;color:#172033;">{escape(title)}</h2>
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-collapse:collapse;">
          {body}
        </table>
      </td>
    </tr>
    """


def render_email_html(preview: AlertPreview, greeting_name: str = "Xinyi", app_url: str = "") -> str:
    run_date = preview.run_date.strftime("%b %d, %Y")
    cta_html = ""
    if app_url:
        cta_html = f"""
        <tr>
          <td style="padding-top:18px;">
            <a href="{escape(app_url, quote=True)}" style="display:inline-block;background:#312e81;color:#ffffff;text-decoration:none;border-radius:10px;padding:12px 18px;font-size:14px;font-weight:700;">Open Credit Card Benefit Tracker</a>
          </td>
        </tr>
        """

    benefits_html = "".join(_benefit_card(row) for _, row in preview.benefits.iterrows())
    fees_html = "".join(_annual_fee_card(row) for _, row in preview.annual_fees.iterrows())

    return f"""<!doctype html>
<html>
  <body style="margin:0;padding:0;background:#f5f7fb;font-family:Arial,Helvetica,sans-serif;color:#172033;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-collapse:collapse;background:#f5f7fb;">
      <tr>
        <td align="center" style="padding:28px 12px;">
          <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-collapse:collapse;max-width:680px;">
            <tr>
              <td style="background:#ffffff;border-radius:18px;padding:26px;border:1px solid #e6e8f3;">
                <div style="font-size:26px;line-height:1.2;font-weight:800;color:#172033;">Credit Card Benefit Reminder</div>
                <div style="font-size:14px;line-height:1.45;color:#64748b;margin-top:6px;">Generated from your tracker on {escape(run_date)}.</div>
                <p style="font-size:15px;line-height:1.55;color:#334155;margin:22px 0 18px 0;">Hi {escape(greeting_name)},</p>
                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-collapse:collapse;background:#f8fafc;border-radius:14px;border:1px solid #e6e8f3;">
                  <tr>
                    <td style="padding:14px;">
                      <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="border-collapse:collapse;">
                        <tr>
                          <td style="font-size:12px;color:#64748b;">Benefits</td>
                          <td style="font-size:12px;color:#64748b;">Remaining value</td>
                          <td style="font-size:12px;color:#64748b;">Annual fees</td>
                          <td style="font-size:12px;color:#64748b;">Most urgent</td>
                        </tr>
                        <tr>
                          <td style="font-size:20px;font-weight:800;color:#312e81;padding-top:4px;">{preview.benefit_count}</td>
                          <td style="font-size:20px;font-weight:800;color:#312e81;padding-top:4px;">{escape(_format_money(preview.total_remaining_value))}</td>
                          <td style="font-size:20px;font-weight:800;color:#b45309;padding-top:4px;">{preview.annual_fee_count}</td>
                          <td style="font-size:14px;font-weight:700;color:#172033;padding-top:4px;">{escape(_most_urgent_date(preview))}</td>
                        </tr>
                      </table>
                    </td>
                  </tr>
                </table>
                {_section("Benefits expiring or resetting soon", benefits_html, "No benefit reminders are due for this run.")}
                {_section("Annual fee reminders", fees_html, "No annual fee reminders are due for this run.")}
                {cta_html}
                <div style="border-top:1px solid #e6e8f3;margin-top:24px;padding-top:14px;font-size:12px;line-height:1.5;color:#64748b;">
                  This reminder was generated from your Credit Card Benefit Tracker. Alerts are based on the latest Google Sheets data available to the alert runner.
                </div>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>"""

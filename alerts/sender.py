from __future__ import annotations

import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from html.parser import HTMLParser


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.parts.append(text)

    def text(self) -> str:
        return "\n".join(self.parts)


@dataclass(frozen=True)
class EmailConfig:
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    sender_email: str
    sender_name: str = "Credit Card Benefit Tracker"
    use_tls: bool = True
    use_ssl: bool = False

    def missing_fields(self) -> list[str]:
        missing = []
        if not self.smtp_host:
            missing.append("ALERT_SMTP_HOST")
        if not self.smtp_port:
            missing.append("ALERT_SMTP_PORT")
        if not self.smtp_username:
            missing.append("ALERT_SMTP_USERNAME")
        if not self.smtp_password:
            missing.append("ALERT_SMTP_PASSWORD")
        if not self.sender_email:
            missing.append("ALERT_SENDER_EMAIL")
        return missing


def html_to_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return parser.text()


def send_html_email(config: EmailConfig, recipient_email: str, subject: str, html_body: str) -> None:
    missing = config.missing_fields()
    if missing:
        raise ValueError(f"Missing email configuration: {', '.join(missing)}")
    if not recipient_email:
        raise ValueError("Missing email configuration: ALERT_RECIPIENT_EMAIL")

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{config.sender_name} <{config.sender_email}>"
    message["To"] = recipient_email
    message.set_content(html_to_text(html_body) or subject)
    message.add_alternative(html_body, subtype="html")

    try:
        if config.use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(config.smtp_host, config.smtp_port, timeout=30, context=context) as server:
                server.login(config.smtp_username, config.smtp_password)
                server.send_message(message)
        elif config.use_tls:
            context = ssl.create_default_context()
            with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=30) as server:
                server.starttls(context=context)
                server.login(config.smtp_username, config.smtp_password)
                server.send_message(message)
        else:
            with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=30) as server:
                server.login(config.smtp_username, config.smtp_password)
                server.send_message(message)
    except smtplib.SMTPAuthenticationError as exc:
        raise RuntimeError(
            "SMTP authentication failed. For Gmail, check that 2-Step Verification is enabled, "
            "ALERT_SMTP_PASSWORD is a Gmail App Password, and ALERT_SMTP_USERNAME / ALERT_SENDER_EMAIL match the sending account."
        ) from exc

from __future__ import annotations

import smtplib
import ssl
from email.mime.text import MIMEText
from email.utils import formataddr

from src.config import AppConfig
from src.models import Contact, DeliveryResult, EmailDraft


class DryRunEmailSender:
    """Simulates sending — returns success, no network I/O."""

    def send(self, draft: EmailDraft, contact: Contact, config: AppConfig) -> DeliveryResult:
        _ = draft, contact, config  # unused in dry-run
        return DeliveryResult(status="drafted", provider_message_id=None, error=None)


class SmtpEmailSender:
    """Delivers email via SMTP with STARTTLS (port 587)."""

    def send(self, draft: EmailDraft, contact: Contact, config: AppConfig) -> DeliveryResult:
        if not config.smtp_user or not config.smtp_password:
            return DeliveryResult(
                status="failed",
                provider_message_id=None,
                error="SMTP_USER and SMTP_PASSWORD must be set when DRY_RUN=false",
            )

        msg = MIMEText(draft.body, _charset="utf-8")
        msg["Subject"] = draft.subject
        msg["From"] = formataddr((config.sender_name or config.smtp_user, config.smtp_user))
        msg["To"] = formataddr(
            (contact.recipient_name or contact.recipient_email, contact.recipient_email)
        )

        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(config.smtp_host, config.smtp_port, timeout=30) as server:
                server.starttls(context=context)
                server.login(config.smtp_user, config.smtp_password)
                server.sendmail(config.smtp_user, [contact.recipient_email], msg.as_string())

            return DeliveryResult(status="sent", provider_message_id=None, error=None)
        except smtplib.SMTPAuthenticationError:
            return DeliveryResult(
                status="failed",
                provider_message_id=None,
                error=(
                    "SMTP authentication failed. If using Gmail, create an App Password "
                    "(google.com/apppasswords) and use it as SMTP_PASSWORD."
                ),
            )
        except smtplib.SMTPException as exc:
            return DeliveryResult(
                status="failed", provider_message_id=None, error=f"SMTP error: {exc}"
            )
        except OSError as exc:
            return DeliveryResult(
                status="failed",
                provider_message_id=None,
                error=f"Connection error: {exc}",
            )


def deliver_email(draft: EmailDraft, contact: Contact, config: AppConfig) -> DeliveryResult:
    """Select sender based on dry_run flag and deliver the email."""
    sender: DryRunEmailSender | SmtpEmailSender
    if config.dry_run:
        sender = DryRunEmailSender()
    else:
        sender = SmtpEmailSender()
    return sender.send(draft, contact, config)

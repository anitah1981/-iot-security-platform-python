"""
services/notification_service.py - Multi-channel notifications (MVP scaffolding)

Supports:
- Email (SendGrid)
- SMS, WhatsApp, Voice Calls (Twilio)

Design goals:
- Safe to import without credentials (no-op with clear error)
- Minimal, composable methods so routes/services can call into it
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class NotificationResult:
    ok: bool
    channel: str
    detail: str


class NotificationService:
    def __init__(self) -> None:
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("FROM_EMAIL")

        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")

    def _sendgrid_ready(self) -> bool:
        return bool(self.sendgrid_api_key and self.from_email)

    def _twilio_ready(self) -> bool:
        return bool(self.twilio_account_sid and self.twilio_auth_token and self.twilio_phone_number)

    def send_email(self, to_email: str, subject: str, content: str) -> NotificationResult:
        if not self._sendgrid_ready():
            return NotificationResult(False, "email", "SendGrid not configured (SENDGRID_API_KEY/FROM_EMAIL)")

        try:
            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail

            message = Mail(
                from_email=self.from_email,
                to_emails=to_email,
                subject=subject,
                plain_text_content=content,
            )
            sg = SendGridAPIClient(self.sendgrid_api_key)
            sg.send(message)
            return NotificationResult(True, "email", "Sent")
        except Exception as e:
            return NotificationResult(False, "email", f"Send failed: {e}")

    def send_sms(self, to_number: str, body: str) -> NotificationResult:
        if not self._twilio_ready():
            return NotificationResult(False, "sms", "Twilio not configured (TWILIO_* env vars)")

        try:
            from twilio.rest import Client

            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            client.messages.create(from_=self.twilio_phone_number, to=to_number, body=body)
            return NotificationResult(True, "sms", "Sent")
        except Exception as e:
            return NotificationResult(False, "sms", f"Send failed: {e}")

    def send_whatsapp(self, to_number: str, body: str) -> NotificationResult:
        if not self._twilio_ready():
            return NotificationResult(False, "whatsapp", "Twilio not configured (TWILIO_* env vars)")

        try:
            from twilio.rest import Client

            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            client.messages.create(
                from_=f"whatsapp:{self.twilio_phone_number}",
                to=f"whatsapp:{to_number}",
                body=body,
            )
            return NotificationResult(True, "whatsapp", "Sent")
        except Exception as e:
            return NotificationResult(False, "whatsapp", f"Send failed: {e}")

    def make_voice_call(self, to_number: str, twiml: Optional[str] = None) -> NotificationResult:
        """
        MVP: uses inline TwiML if provided, otherwise a simple default message.
        """
        if not self._twilio_ready():
            return NotificationResult(False, "voice", "Twilio not configured (TWILIO_* env vars)")

        try:
            from twilio.rest import Client

            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            twiml_payload = twiml or "<Response><Say>Critical alert from IoT Security Platform.</Say></Response>"
            client.calls.create(from_=self.twilio_phone_number, to=to_number, twiml=twiml_payload)
            return NotificationResult(True, "voice", "Call placed")
        except Exception as e:
            return NotificationResult(False, "voice", f"Call failed: {e}")


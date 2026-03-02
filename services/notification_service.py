"""
services/notification_service.py - Multi-channel notifications (MVP scaffolding)

Supports:
- Email (Gmail SMTP)
- SMS, WhatsApp, Voice Calls (Twilio)

Design goals:
- Safe to import without credentials (no-op with clear error)
- Minimal, composable methods so routes/services can call into it
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass(frozen=True)
class NotificationResult:
    ok: bool
    channel: str
    detail: str
    error_code: Optional[str] = None


# Helper function for simple email sending
async def send_email(to_email: str, subject: str, body: str) -> NotificationResult:
    """
    Simple helper function to send an email
    """
    service = NotificationService()
    return await service._send_email(to_email, subject, body)


class NotificationService:
    def __init__(self) -> None:
        # Gmail SMTP Configuration
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL")

        self.twilio_account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.twilio_auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.twilio_phone_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.twilio_whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")
        # Default SMS to enabled when Twilio is configured (set SMS_ENABLED=false to disable)
        _sms_env = os.getenv("SMS_ENABLED", "").strip().lower()
        if _sms_env in ("0", "false", "no", "off"):
            self.sms_enabled = False
        elif _sms_env in ("1", "true", "yes", "on"):
            self.sms_enabled = True
        else:
            self.sms_enabled = bool(self.twilio_account_sid and self.twilio_auth_token and self.twilio_phone_number)

    def _smtp_ready(self) -> bool:
        return bool(self.smtp_user and self.smtp_password and self.from_email)

    def _twilio_base_ready(self) -> bool:
        return bool(self.twilio_account_sid and self.twilio_auth_token)

    def _sms_ready(self) -> bool:
        return bool(self.sms_enabled and self._twilio_base_ready() and self.twilio_phone_number)

    def _voice_ready(self) -> bool:
        return bool(self._twilio_base_ready() and self.twilio_phone_number)

    def _whatsapp_ready(self) -> bool:
        return bool(self._twilio_base_ready() and (self.twilio_whatsapp_number or self.twilio_phone_number))

    def _format_whatsapp_from(self) -> Optional[str]:
        number = self.twilio_whatsapp_number or self.twilio_phone_number
        if not number:
            return None
        return number if number.startswith("whatsapp:") else f"whatsapp:{number}"

    @staticmethod
    def _format_whatsapp_to(to_number: str) -> str:
        return to_number if to_number.startswith("whatsapp:") else f"whatsapp:{to_number}"

    async def _send_email(
        self,
        to_email: str,
        subject: str,
        message: str,
        severity: str,
        alert_id: str,
        *,
        body_is_html: bool = False,
    ) -> bool:
        """Send email via Gmail SMTP. If body_is_html=True, message is sent as-is (full HTML). Otherwise use alert template."""
        if not self.smtp_user or not self.smtp_password:
            print("[WARNING] Gmail SMTP not configured - skipping email")
            return False
        if not self.from_email:
            print("[WARNING] FROM_EMAIL not set - cannot send email")
            return False
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            if body_is_html:
                html_content = message
            else:
                html_content = f"""
                <html>
                    <body style="font-family: Arial, sans-serif; padding: 20px;">
                        <div style="background: {'#dc2626' if severity == 'critical' else '#f59e0b' if severity == 'high' else '#3b82f6'};
                                    color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                            <h2 style="margin: 0;">🚨 Pro-Alert Alert</h2>
                        </div>
                        <div style="background: #f3f4f6; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                            <p style="font-size: 18px; margin: 0;"><strong>{message}</strong></p>
                        </div>
                        <p><strong>Severity:</strong> {severity.upper()}</p>
                        <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                        <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                        <p style="color: #6b7280; font-size: 12px;">You're receiving this because you have Pro-Alert monitoring enabled.</p>
                    </body>
                </html>
                """
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            msg.attach(MIMEText(html_content, 'html'))
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            print(f"[OK] Email sent to {to_email}")
            return True
        except Exception as e:
            import traceback
            print(f"[ERROR] Email error: {e}")
            traceback.print_exc()
            return False

    def send_email(self, to_email: str, subject: str, content: str) -> NotificationResult:
        if not self._smtp_ready():
            return NotificationResult(False, "email", "Gmail SMTP not configured (SMTP_USER/SMTP_PASSWORD/FROM_EMAIL)")

        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            # Create message
            message = MIMEMultipart()
            message["From"] = self.from_email
            message["To"] = to_email
            message["Subject"] = subject
            message.attach(MIMEText(content, "plain"))

            # Send via Gmail SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(message)
            
            return NotificationResult(True, "email", "Sent")
        except Exception as e:
            return NotificationResult(False, "email", f"Send failed: {e}")

    def send_sms(self, to_number: str, body: str) -> NotificationResult:
        if not self.sms_enabled:
            return NotificationResult(
                False,
                "sms",
                "SMS disabled by server configuration (SMS_ENABLED=false)",
                "SMS_DISABLED",
            )
        if not self._sms_ready():
            return NotificationResult(
                False,
                "sms",
                "Twilio not configured (TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN/TWILIO_PHONE_NUMBER)",
            )

        try:
            from twilio.rest import Client

            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            client.messages.create(from_=self.twilio_phone_number, to=to_number, body=body)
            return NotificationResult(True, "sms", "Sent")
        except ModuleNotFoundError as e:
            if "twilio" in str(e).lower():
                return NotificationResult(False, "sms", "Twilio package not installed. Run: pip install twilio")
            return NotificationResult(False, "sms", f"Send failed: {e}")
        except Exception as e:
            error_code = getattr(e, "code", None)
            if error_code == 21608:
                return NotificationResult(False, "sms", "We couldn't reach this number. Please check it is correct and try again.", "21608")
            if error_code:
                detail = f"Twilio error {error_code}: {getattr(e, 'msg', str(e))}"
                return NotificationResult(False, "sms", detail, str(error_code))
            return NotificationResult(False, "sms", f"Send failed: {e}")

    def send_whatsapp(self, to_number: str, body: str) -> NotificationResult:
        if not self._whatsapp_ready():
            return NotificationResult(
                False,
                "whatsapp",
                "Twilio not configured (TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN + TWILIO_WHATSAPP_NUMBER or TWILIO_PHONE_NUMBER)",
            )

        try:
            from twilio.rest import Client

            from_number = self._format_whatsapp_from()
            if not from_number:
                return NotificationResult(
                    False,
                    "whatsapp",
                    "Twilio WhatsApp sender not configured (TWILIO_WHATSAPP_NUMBER or TWILIO_PHONE_NUMBER)",
                )

            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            client.messages.create(
                from_=from_number,
                to=self._format_whatsapp_to(to_number),
                body=body,
            )
            return NotificationResult(True, "whatsapp", "Sent")
        except ModuleNotFoundError as e:
            if "twilio" in str(e).lower():
                return NotificationResult(False, "whatsapp", "Twilio package not installed. Run: pip install twilio")
            return NotificationResult(False, "whatsapp", f"Send failed: {e}")
        except Exception as e:
            code = getattr(e, "code", None) or getattr(e, "status", None)
            if code == 63016:
                return NotificationResult(False, "whatsapp", "WhatsApp couldn't be delivered. Please ensure you've accepted messages from this service and try again.", "63016")
            if code:
                return NotificationResult(False, "whatsapp", f"WhatsApp error {code}: {getattr(e, 'msg', str(e))}", str(code))
            return NotificationResult(False, "whatsapp", f"Send failed: {e}")

    def make_voice_call(self, to_number: str, twiml: Optional[str] = None) -> NotificationResult:
        """
        MVP: uses inline TwiML if provided, otherwise a simple default message.
        """
        if not self._voice_ready():
            return NotificationResult(
                False,
                "voice",
                "Twilio not configured (TWILIO_ACCOUNT_SID/TWILIO_AUTH_TOKEN/TWILIO_PHONE_NUMBER)",
            )

        try:
            from twilio.rest import Client

            client = Client(self.twilio_account_sid, self.twilio_auth_token)
            twiml_payload = twiml or "<Response><Say>This is an automated notification. A device on your account has gone offline. Please check your dashboard.</Say></Response>"
            client.calls.create(from_=self.twilio_phone_number, to=to_number, twiml=twiml_payload)
            return NotificationResult(True, "voice", "Call placed")
        except ModuleNotFoundError as e:
            if "twilio" in str(e).lower():
                return NotificationResult(False, "voice", "Twilio package not installed. Run: pip install twilio")
            return NotificationResult(False, "voice", f"Call failed: {e}")
        except Exception as e:
            code = getattr(e, "code", None) or getattr(e, "status", None)
            if code == 21608:
                return NotificationResult(False, "voice", "We couldn't place a call to this number. Please check it is correct and try again.", "21608")
            if code:
                return NotificationResult(False, "voice", f"Voice error {code}: {getattr(e, 'msg', str(e))}", str(code))
            return NotificationResult(False, "voice", f"Call failed: {e}")


# Singleton instance
_notification_service = NotificationService()


def get_notification_service() -> NotificationService:
    """Get the global notification service instance"""
    return _notification_service


async def send_alert_notification(
    user_email: str,
    user_name: str,
    device_name: str,
    alert_message: str,
    alert_severity: str,
    notification_prefs: dict,
    alert_id: str = "unknown"
) -> list[NotificationResult]:
    """
    Send notifications based on user preferences and alert severity
    
    Args:
        user_email: User's email address
        user_name: User's name
        device_name: Name of the device that triggered the alert
        alert_message: The alert message
        alert_severity: Alert severity (low, medium, high, critical)
        notification_prefs: User's notification preferences from DB
        alert_id: ID of the alert (optional)
    
    Returns:
        List of notification results
    """
    service = get_notification_service()
    results = []
    
    # Log so we can see why a channel might not fire (e.g. SMTP not configured, no phone number)
    print(f"[NOTIFY] Alert to {user_email} | device={device_name} severity={alert_severity} | "
          f"email={notification_prefs.get('emailEnabled', True)} sms={notification_prefs.get('smsEnabled')} phone={bool(notification_prefs.get('phoneNumber'))} "
          f"whatsapp={notification_prefs.get('whatsappEnabled')} wa_num={bool(notification_prefs.get('whatsappNumber'))} voice={notification_prefs.get('voiceEnabled')}")
    
    # Format the alert message for email
    subject = f"[{alert_severity.upper()}] Pro-Alert Alert - {device_name}"
    email_message = f"Device: {device_name}\n\n{alert_message}"
    
    # Check if in quiet hours
    if notification_prefs.get("quietHoursEnabled", False):
        from datetime import datetime
        now = datetime.utcnow()
        quiet_start = notification_prefs.get("quietHoursStart")
        quiet_end = notification_prefs.get("quietHoursEnd")
        
        if quiet_start and quiet_end:
            # Parse time strings (format: "HH:MM")
            try:
                start_hour, start_min = map(int, quiet_start.split(":"))
                end_hour, end_min = map(int, quiet_end.split(":"))
                
                current_hour = now.hour
                current_min = now.minute
                current_time_minutes = current_hour * 60 + current_min
                start_time_minutes = start_hour * 60 + start_min
                end_time_minutes = end_hour * 60 + end_min
                
                # Check if current time is in quiet hours
                in_quiet_hours = False
                if start_time_minutes > end_time_minutes:
                    # Quiet hours span midnight (e.g., 22:00 to 07:00)
                    in_quiet_hours = current_time_minutes >= start_time_minutes or current_time_minutes < end_time_minutes
                else:
                    # Quiet hours within same day (e.g., 22:00 to 23:00)
                    in_quiet_hours = start_time_minutes <= current_time_minutes < end_time_minutes
                
                # Skip non-critical alerts during quiet hours
                if in_quiet_hours and alert_severity != "critical":
                    # Suppress non-critical alerts during quiet hours
                    return [NotificationResult(True, "email", "Suppressed (quiet hours)")]
            except (ValueError, AttributeError):
                # Invalid time format, skip quiet hours check
                pass
    
    # Email notification - using new HTML email
    if notification_prefs.get("emailEnabled", True):
        email_severities = notification_prefs.get("emailSeverities", ["low", "medium", "high", "critical"])
        if alert_severity in email_severities:
            success = await service._send_email(
                to_email=user_email,
                subject=subject,
                message=email_message,
                severity=alert_severity,
                alert_id=alert_id
            )
            results.append(NotificationResult(success, "email", "Sent" if success else "Failed"))
    
    # SMS notification
    sms_enabled = notification_prefs.get("smsEnabled", False) in (True, "true", "1", 1, "yes", "on")
    phone_number = (notification_prefs.get("phoneNumber") or "").strip() or None
    if sms_enabled:
        sms_severities = notification_prefs.get("smsSeverities", ["high", "critical"])
        if alert_severity not in sms_severities:
            results.append(NotificationResult(False, "sms", "Skipped (severity not in sms severities)"))
        elif not phone_number:
            print("[NOTIFY] Skipping SMS: no phone number in preferences")
            results.append(NotificationResult(False, "sms", "Skipped (no phone number)"))
        else:
            print(f"[NOTIFY] Attempting SMS to {phone_number[:4]}***{phone_number[-2:] if len(phone_number) > 6 else '***'}")
            sms_body = f"Alert: {device_name} has gone offline. Please check your network or dashboard."
            result = service.send_sms(phone_number, sms_body)
            results.append(result)
    else:
        results.append(NotificationResult(False, "sms", "Skipped (SMS disabled in prefs)"))
    
    # WhatsApp notification
    wa_enabled = notification_prefs.get("whatsappEnabled", False) in (True, "true", "1", 1, "yes", "on")
    whatsapp_number = (notification_prefs.get("whatsappNumber") or "").strip() or None
    if wa_enabled:
        whatsapp_severities = notification_prefs.get("whatsappSeverities", ["medium", "high", "critical"])
        if alert_severity not in whatsapp_severities:
            results.append(NotificationResult(False, "whatsapp", "Skipped (severity not in whatsapp severities)"))
        elif not whatsapp_number:
            print("[NOTIFY] Skipping WhatsApp: no WhatsApp number in preferences")
            results.append(NotificationResult(False, "whatsapp", "Skipped (no whatsapp number)"))
        else:
            print(f"[NOTIFY] Attempting WhatsApp to {whatsapp_number[:4]}***{whatsapp_number[-2:] if len(whatsapp_number) > 6 else '***'}")
            wa_body = f"Alert: {device_name} has gone offline. Please check your WiFi or dashboard."
            result = service.send_whatsapp(whatsapp_number, wa_body)
            results.append(result)
    else:
        results.append(NotificationResult(False, "whatsapp", "Skipped (WhatsApp disabled in prefs)"))
    
    # Voice call for critical
    voice_enabled = notification_prefs.get("voiceEnabled", False) in (True, "true", "1", 1, "yes", "on")
    if voice_enabled:
        voice_severities = notification_prefs.get("voiceSeverities", ["critical"])
        if alert_severity not in voice_severities:
            results.append(NotificationResult(False, "voice", "Skipped (severity not in voice severities)"))
        elif not phone_number:
            print("[NOTIFY] Skipping Voice: no phone number in preferences")
            results.append(NotificationResult(False, "voice", "Skipped (no phone number)"))
        else:
            print(f"[NOTIFY] Attempting Voice call to {phone_number[:4]}***{phone_number[-2:] if len(phone_number) > 6 else '***'}")
            twiml = f"<Response><Say>This is an automated notification. Your device {device_name} has gone offline. Please check your WiFi or dashboard.</Say></Response>"
            result = service.make_voice_call(phone_number, twiml)
            results.append(result)
    else:
        results.append(NotificationResult(False, "voice", "Skipped (Voice disabled in prefs)"))
    
    return results

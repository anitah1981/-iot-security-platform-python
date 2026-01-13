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

    def _smtp_ready(self) -> bool:
        return bool(self.smtp_user and self.smtp_password and self.from_email)

    def _twilio_ready(self) -> bool:
        return bool(self.twilio_account_sid and self.twilio_auth_token and self.twilio_phone_number)

    async def _send_email(
        self,
        to_email: str,
        subject: str,
        message: str,
        severity: str,
        alert_id: str
    ) -> bool:
        """Send email notification via Gmail SMTP with HTML formatting"""
        
        if not self.smtp_user or not self.smtp_password:
            print("[WARNING] Gmail SMTP not configured - skipping email")
            return False
        
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Create HTML email body
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px;">
                    <div style="background: {'#dc2626' if severity == 'critical' else '#f59e0b' if severity == 'high' else '#3b82f6'}; 
                                color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                        <h2 style="margin: 0;">🚨 IoT Security Alert</h2>
                    </div>
                    
                    <div style="background: #f3f4f6; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                        <p style="font-size: 18px; margin: 0;"><strong>{message}</strong></p>
                    </div>
                    
                    <p><strong>Severity:</strong> {severity.upper()}</p>
                    <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
                    
                    <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
                    
                    <p style="color: #6b7280; font-size: 12px;">
                        You're receiving this because you have IoT Security Platform monitoring enabled.
                    </p>
                </body>
            </html>
            """
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send via Gmail SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            print(f"[OK] Email sent to {to_email}")
            return True
        
        except Exception as e:
            print(f"[ERROR] Email error: {e}")
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
    
    # Format the alert message for email
    subject = f"[{alert_severity.upper()}] IoT Security Alert - {device_name}"
    email_message = f"Device: {device_name}\n\n{alert_message}"
    
    # Check if in quiet hours
    if notification_prefs.get("quietHoursEnabled", False):
        from datetime import datetime
        now = datetime.utcnow()
        # TODO: Implement quiet hours check
        # For now, skip quiet hours for critical alerts
        if alert_severity != "critical":
            # Would check time here
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
    if notification_prefs.get("smsEnabled", False):
        sms_severities = notification_prefs.get("smsSeverities", ["high", "critical"])
        phone_number = notification_prefs.get("phoneNumber")
        if alert_severity in sms_severities and phone_number:
            sms_body = f"[{alert_severity.upper()}] {device_name}: {alert_message}"
            result = service.send_sms(phone_number, sms_body)
            results.append(result)
    
    # WhatsApp notification
    if notification_prefs.get("whatsappEnabled", False):
        whatsapp_severities = notification_prefs.get("whatsappSeverities", ["medium", "high", "critical"])
        whatsapp_number = notification_prefs.get("whatsappNumber")
        if alert_severity in whatsapp_severities and whatsapp_number:
            wa_body = f"🚨 [{alert_severity.upper()}] Alert\n\nDevice: {device_name}\n{alert_message}"
            result = service.send_whatsapp(whatsapp_number, wa_body)
            results.append(result)
    
    # Voice call for critical
    if notification_prefs.get("voiceEnabled", False):
        voice_severities = notification_prefs.get("voiceSeverities", ["critical"])
        phone_number = notification_prefs.get("phoneNumber")
        if alert_severity in voice_severities and phone_number:
            twiml = f"<Response><Say>Critical alert from I o T Security Platform. {device_name} {alert_message}. Please check your dashboard immediately.</Say></Response>"
            result = service.make_voice_call(phone_number, twiml)
            results.append(result)
    
    return results

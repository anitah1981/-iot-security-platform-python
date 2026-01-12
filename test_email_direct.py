"""Direct email test - bypasses the API to test SMTP directly"""
import os
from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL")

print("="*60)
print("  Direct SMTP Email Test")
print("="*60)
print(f"\nConfiguration:")
print(f"  SMTP Host: {SMTP_HOST}")
print(f"  SMTP Port: {SMTP_PORT}")
print(f"  SMTP User: {SMTP_USER}")
print(f"  From Email: {FROM_EMAIL}")
print(f"  Password: {'*' * len(SMTP_PASSWORD) if SMTP_PASSWORD else 'NOT SET'}")

if not SMTP_USER or not SMTP_PASSWORD:
    print("\n❌ ERROR: SMTP credentials not set in .env file!")
    exit(1)

print("\n" + "="*60)
print("  Sending test email...")
print("="*60)

try:
    # Create HTML email
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <div style="background: #f59e0b; color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <h2 style="margin: 0;">🚨 IoT Security Alert - SMTP TEST</h2>
            </div>
            
            <div style="background: #f3f4f6; padding: 20px; border-radius: 5px; margin-bottom: 20px;">
                <p style="font-size: 18px; margin: 0;"><strong>This is a direct SMTP test email from your IoT Security Platform!</strong></p>
            </div>
            
            <p><strong>Status:</strong> If you're reading this, your email configuration is working perfectly! ✅</p>
            <p><strong>Time:</strong> {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #e5e7eb;">
            
            <p style="color: #6b7280; font-size: 12px;">
                This is a test email from IoT Security Platform
            </p>
        </body>
    </html>
    """
    
    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "🧪 IoT Security Platform - SMTP Test Email"
    msg['From'] = FROM_EMAIL
    msg['To'] = SMTP_USER  # Send to yourself
    
    html_part = MIMEText(html_content, 'html')
    msg.attach(html_part)
    
    # Send via Gmail SMTP
    print(f"\nConnecting to {SMTP_HOST}:{SMTP_PORT}...")
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        print("✅ Connected!")
        
        print("Starting TLS encryption...")
        server.starttls()
        print("✅ TLS enabled!")
        
        print(f"Logging in as {SMTP_USER}...")
        server.login(SMTP_USER, SMTP_PASSWORD)
        print("✅ Logged in!")
        
        print(f"Sending email to {SMTP_USER}...")
        server.send_message(msg)
        print("✅ Email sent!")
    
    print("\n" + "="*60)
    print("  ✅ SUCCESS!")
    print("="*60)
    print(f"\n📧 Check your inbox: {SMTP_USER}")
    print("   (Check spam folder if not in inbox)")
    print("\nIf you received this email, your SMTP configuration is working perfectly!")
    print("The IoT Security Platform can now send notifications! 🎉")
    
except smtplib.SMTPAuthenticationError as e:
    print("\n" + "="*60)
    print("  ❌ AUTHENTICATION ERROR")
    print("="*60)
    print("\nYour Gmail credentials are incorrect or expired.")
    print("\n Fix:")
    print("  1. Go to: https://myaccount.google.com/apppasswords")
    print("  2. Generate a NEW app password")
    print("  3. Update SMTP_PASSWORD in your .env file")
    print(f"\nError details: {e}")
    
except Exception as e:
    print("\n" + "="*60)
    print("  ❌ ERROR")
    print("="*60)
    print(f"\nError: {e}")
    print(f"Type: {type(e).__name__}")

print("\n")

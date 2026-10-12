import os
import smtplib
import mimetypes
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

class EmailService:
    def __init__(self):
        self.root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    def _get_smtp_config(self):
        return {
            "provider": os.getenv("EMAIL_PROVIDER", "smtp"),
            "host": os.getenv("SMTP_HOST", ""),
            "port": int(os.getenv("SMTP_PORT", 587)),
            "username": os.getenv("SMTP_USERNAME", ""),
            "password": os.getenv("SMTP_PASSWORD", ""),
            "from_email": os.getenv("SMTP_FROM", "noreply@cognifocus.ai")
        }

    def is_configured(self):
        cfg = self._get_smtp_config()
        return bool(cfg["host"] and cfg["username"] and cfg["password"])

    def send_alert_email(self, recipient_email, alert_data):
        """
        Sends real-time email notification with attached student evidence screenshot.
        Non-blocking execution handled by NotificationService.
        """
        cfg = self._get_smtp_config()
        if not recipient_email or not recipient_email.strip():
            return False, "Recipient email is empty"

        if not self.is_configured():
            print(f"[EmailService] Email notifications: NOT CONFIGURED for {recipient_email}. (Missing SMTP host/credentials in .env)")
            return False, "Email notifications: NOT CONFIGURED"

        classroom_id = alert_data.get('classroom_id') or 'CSE-301'
        classroom_code = alert_data.get('classroom_code') or alert_data.get('classroom_id') or 'CSE301'
        classroom_name = alert_data.get('classroom_name') or f"Computer Science Hall {classroom_code}"
        seat_id = alert_data.get('seat_id') or alert_data.get('seat') or 'N/A'
        student_id = alert_data.get('student_id') or 'N/A'
        alert_type = alert_data.get('alert_type') or 'Mobile Usage'
        duration = alert_data.get('duration') or 10
        camera_id = alert_data.get('camera_id') or 'CAM001'
        timestamp = alert_data.get('timestamp') or 'Recent'
        status = alert_data.get('status') or 'Active'

        subject = f"🚨 CogniFocus-AI Alert — Mobile Usage Detected — {classroom_code}"

        text_body = f"""CogniFocus-AI Classroom Monitoring Alert

Classroom:
{classroom_id} ({classroom_code})

Classroom Name:
{classroom_name}

Seat:
{seat_id}

Student:
{student_id}

Alert Type:
{alert_type}

Duration:
{duration} seconds

Camera:
{camera_id}

Time:
{timestamp}

Status:
{status}

A student has been detected using a mobile phone for more than the configured threshold.
Please check the CogniFocus-AI dashboard for additional information.
"""

        html_body = f"""
        <html>
          <body style="font-family: Arial, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #1e293b; border: 1px solid #334155; border-radius: 12px; padding: 24px;">
              <h2 style="color: #f43f5e; margin-top: 0;">🚨 CogniFocus-AI Alert Notification</h2>
              <p style="color: #94a3b8; font-size: 14px;">Mobile phone usage detected exceeding safety threshold.</p>
              
              <table style="width: 100%; border-collapse: collapse; margin-top: 16px; font-size: 14px; color: #e2e8f0;">
                <tr style="border-b: 1px solid #334155;"><td style="padding: 8px; font-weight: bold; color: #38bdf8;">Classroom</td><td style="padding: 8px;">{classroom_id} ({classroom_name})</td></tr>
                <tr style="border-b: 1px solid #334155;"><td style="padding: 8px; font-weight: bold; color: #38bdf8;">Seat / Student</td><td style="padding: 8px;">Seat {seat_id} &bull; {student_id}</td></tr>
                <tr style="border-b: 1px solid #334155;"><td style="padding: 8px; font-weight: bold; color: #38bdf8;">Alert Type</td><td style="padding: 8px; color: #fb7185; font-weight: bold;">{alert_type}</td></tr>
                <tr style="border-b: 1px solid #334155;"><td style="padding: 8px; font-weight: bold; color: #38bdf8;">Duration</td><td style="padding: 8px; font-weight: bold; color: #f43f5e;">{duration} seconds</td></tr>
                <tr style="border-b: 1px solid #334155;"><td style="padding: 8px; font-weight: bold; color: #38bdf8;">Camera</td><td style="padding: 8px;">{camera_id}</td></tr>
                <tr style="border-b: 1px solid #334155;"><td style="padding: 8px; font-weight: bold; color: #38bdf8;">Time</td><td style="padding: 8px;">{timestamp}</td></tr>
              </table>

              <p style="margin-top: 20px; font-size: 13px; color: #94a3b8;">
                The evidence crop frame is attached below. Log into the CogniFocus-AI Dashboard for live feed stream.
              </p>
            </div>
          </body>
        </html>
        """

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = cfg["from_email"]
        msg['To'] = recipient_email

        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))

        # Attach Evidence Image (Section 5)
        evidence_path = alert_data.get('evidence_image')
        if evidence_path:
            full_path = os.path.join(self.root_dir, "backend", evidence_path.lstrip('/'))
            if os.path.exists(full_path) and os.path.getsize(full_path) > 0:
                try:
                    with open(full_path, 'rb') as img_f:
                        img_data = img_f.read()
                        image_part = MIMEImage(img_data, name=os.path.basename(full_path))
                        image_part.add_header('Content-ID', '<evidence_crop>')
                        msg.attach(image_part)
                        print(f"[EmailService] Evidence screenshot attached to email: {full_path}")
                except Exception as img_err:
                    print(f"[EmailService] Failed to attach evidence image: {img_err}")

        try:
            with smtplib.SMTP(cfg["host"], cfg["port"], timeout=10) as server:
                if cfg["port"] in [587, 25]:
                    server.starttls()
                server.login(cfg["username"], cfg["password"])
                server.sendmail(cfg["from_email"], [recipient_email], msg.as_string())

            print(f"[EmailService] Real-time email alert SENT to {recipient_email}")
            return True, None
        except Exception as e:
            err_msg = str(e)
            print(f"[EmailService] ERROR: Email delivery failed to {recipient_email}: {err_msg}")
            return False, err_msg

    def send_test_email(self, recipient_email):
        cfg = self._get_smtp_config()
        if not recipient_email or not recipient_email.strip():
            return False, "Recipient email is required"

        if not self.is_configured():
            return False, "Email notifications: NOT CONFIGURED (Missing SMTP credentials in .env)"

        subject = "CogniFocus-AI — Email Notification Test"
        text_body = "CogniFocus-AI test notification.\nYour Email alert configuration is working correctly!"

        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = cfg["from_email"]
        msg['To'] = recipient_email
        msg.attach(MIMEText(text_body, 'plain'))

        try:
            with smtplib.SMTP(cfg["host"], cfg["port"], timeout=10) as server:
                if cfg["port"] in [587, 25]:
                    server.starttls()
                server.login(cfg["username"], cfg["password"])
                server.sendmail(cfg["from_email"], [recipient_email], msg.as_string())
            return True, None
        except Exception as e:
            return False, str(e)

email_service = EmailService()

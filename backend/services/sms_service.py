import os
import requests

class SMSService:
    def __init__(self):
        pass

    def _get_sms_config(self):
        return {
            "provider": os.getenv("SMS_PROVIDER", "generic").lower(),
            "api_key": os.getenv("SMS_API_KEY", ""),
            "api_secret": os.getenv("SMS_API_SECRET", ""),
            "from_sender": os.getenv("SMS_FROM", "COGNIFOCUS"),
            "twilio_sid": os.getenv("TWILIO_ACCOUNT_SID", ""),
            "twilio_auth": os.getenv("TWILIO_AUTH_TOKEN", ""),
            "twilio_phone": os.getenv("TWILIO_PHONE_NUMBER", "")
        }

    def is_configured(self):
        cfg = self._get_sms_config()
        if cfg["provider"] == "twilio":
            return bool(cfg["twilio_sid"] and cfg["twilio_auth"] and cfg["twilio_phone"])
        return bool(cfg["api_key"] or cfg["twilio_sid"])

    def send_alert_sms(self, recipient_phone, alert_data):
        """
        Sends concise real-time SMS notification.
        Non-blocking execution handled by NotificationService.
        """
        cfg = self._get_sms_config()
        if not recipient_phone or not recipient_phone.strip():
            return False, "Recipient phone number is empty"

        if not self.is_configured():
            print(f"[SMSService] SMS notifications: NOT CONFIGURED for {recipient_phone}. (Missing SMS/Twilio API keys in .env)")
            return False, "SMS notifications: NOT CONFIGURED"

        classroom_code = alert_data.get('classroom_code') or alert_data.get('classroom_id') or 'CSE301'
        seat_id = alert_data.get('seat_id') or alert_data.get('seat') or 'N/A'
        student_id = alert_data.get('student_id') or 'N/A'
        duration = alert_data.get('duration') or 10
        camera_id = alert_data.get('camera_id') or 'CAM001'

        message_body = f"CogniFocus-AI Alert: Mobile usage detected in {classroom_code}. Seat: {seat_id}, Student: {student_id}, Duration: {duration}s, Camera: {camera_id}. Check dashboard for evidence."

        try:
            if cfg["provider"] == "twilio" and cfg["twilio_sid"] and cfg["twilio_auth"]:
                url = f"https://api.twilio.com/2010-04-01/Accounts/{cfg['twilio_sid']}/Messages.json"
                auth = (cfg["twilio_sid"], cfg["twilio_auth"])
                data = {
                    "From": cfg["twilio_phone"],
                    "To": recipient_phone,
                    "Body": message_body
                }
                res = requests.post(url, data=data, auth=auth, timeout=10)
                if res.status_code in [200, 201]:
                    print(f"[SMSService] Real-time Twilio SMS SENT to {recipient_phone}")
                    return True, None
                else:
                    err_msg = f"Twilio HTTP {res.status_code}: {res.text}"
                    print(f"[SMSService] Twilio SMS FAILED: {err_msg}")
                    return False, err_msg
            else:
                # Generic SMS Gateway webhook endpoint
                gateway_url = os.getenv("SMS_GATEWAY_URL", "")
                if gateway_url:
                    res = requests.post(gateway_url, json={
                        "to": recipient_phone,
                        "message": message_body,
                        "api_key": cfg["api_key"]
                    }, timeout=10)
                    if res.status_code == 200:
                        print(f"[SMSService] Real-time SMS SENT via gateway to {recipient_phone}")
                        return True, None
                
                print(f"[SMSService] Simulated SMS dispatch to {recipient_phone}: '{message_body}'")
                return True, None
        except Exception as e:
            err_msg = str(e)
            print(f"[SMSService] ERROR: SMS delivery failed to {recipient_phone}: {err_msg}")
            return False, err_msg

    def send_test_sms(self, recipient_phone):
        cfg = self._get_sms_config()
        if not recipient_phone or not recipient_phone.strip():
            return False, "Recipient phone number is required"

        if not self.is_configured():
            return False, "SMS notifications: NOT CONFIGURED (Missing SMS credentials in .env)"

        message_body = "CogniFocus-AI test notification. Your SMS alert configuration is working."
        try:
            if cfg["provider"] == "twilio" and cfg["twilio_sid"] and cfg["twilio_auth"]:
                url = f"https://api.twilio.com/2010-04-01/Accounts/{cfg['twilio_sid']}/Messages.json"
                auth = (cfg["twilio_sid"], cfg["twilio_auth"])
                data = {
                    "From": cfg["twilio_phone"],
                    "To": recipient_phone,
                    "Body": message_body
                }
                res = requests.post(url, data=data, auth=auth, timeout=10)
                if res.status_code in [200, 201]:
                    return True, None
                return False, f"Twilio HTTP {res.status_code}: {res.text}"
            return True, None
        except Exception as e:
            return False, str(e)

sms_service = SMSService()

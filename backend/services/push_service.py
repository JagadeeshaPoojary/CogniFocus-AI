import os
import sys
import json
import sqlite3
import base64
from py_vapid import Vapid
from pywebpush import webpush, WebPushException
from cryptography.hazmat.primitives import serialization

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from database.db import get_db_connection
except ImportError:
    from backend.database.db import get_db_connection

class PushService:
    def __init__(self):
        self._init_vapid_keys()

    def _init_vapid_keys(self):
        """Ensures VAPID keys exist in SQLite configurations table or generates new pair."""
        try:
            config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config')
            os.makedirs(config_dir, exist_ok=True)
            self.private_key_file = os.path.join(config_dir, 'vapid_private.pem')

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM configurations WHERE key IN ('vapid_private_key', 'vapid_public_key')")
            rows = dict(cursor.fetchall())

            if 'vapid_private_key' in rows and 'vapid_public_key' in rows and os.path.exists(self.private_key_file):
                self.private_key_pem = rows['vapid_private_key']
                self.public_key_b64 = rows['vapid_public_key']
                conn.close()
                return

            # Generate new VAPID keys if not present
            vapid = Vapid()
            vapid.generate_keys()
            vapid.save_key(self.private_key_file)

            private_pem = vapid.private_pem().decode('utf-8')
            raw_pub = vapid.public_key.public_bytes(
                encoding=serialization.Encoding.X962,
                format=serialization.PublicFormat.UncompressedPoint
            )
            public_b64 = base64.urlsafe_b64encode(raw_pub).decode('utf-8').rstrip('=')

            cursor.execute("INSERT OR REPLACE INTO configurations (key, value) VALUES ('vapid_private_key', ?)", (private_pem,))
            cursor.execute("INSERT OR REPLACE INTO configurations (key, value) VALUES ('vapid_public_key', ?)", (public_b64,))
            conn.commit()
            conn.close()

            self.private_key_pem = private_pem
            self.public_key_b64 = public_b64
            print("[PushService] Successfully generated and saved VAPID key pair.")
        except Exception as e:
            print(f"[PushService] Error initializing VAPID keys: {e}")
            self.private_key_pem = None
            self.public_key_b64 = None

    def get_public_key(self):
        return self.public_key_b64

    def save_subscription(self, teacher_id, subscription_info):
        endpoint = subscription_info.get('endpoint')
        keys = subscription_info.get('keys', {})
        p256dh = keys.get('p256dh')
        auth = keys.get('auth')

        if not endpoint or not p256dh or not auth:
            return False, "Invalid subscription parameters"

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO teacher_push_subscriptions (teacher_id, endpoint, p256dh, auth)
                VALUES (?, ?, ?, ?)
            """, (teacher_id, endpoint, p256dh, auth))
            conn.commit()
            conn.close()
            return True, None
        except Exception as e:
            print(f"[PushService] Error saving push subscription for teacher {teacher_id}: {e}")
            return False, str(e)

    def send_push_to_teacher(self, teacher_id, alert_data):
        if not self.private_key_pem or not hasattr(self, 'private_key_file') or not os.path.exists(self.private_key_file):
            print("[PushService] VAPID keys not configured, skipping push.")
            return

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, endpoint, p256dh, auth FROM teacher_push_subscriptions
                WHERE teacher_id = ? OR strftime('%s', teacher_id) = strftime('%s', ?)
            """, (teacher_id, str(teacher_id)))
            subscriptions = cursor.fetchall()
            conn.close()

            if not subscriptions:
                return

            payload = json.dumps({
                "title": "🚨 Classroom Alert",
                "body": f"Classroom {alert_data.get('classroom_id', '')}: Student {alert_data.get('student_id', '')} ({alert_data.get('alert_type', 'Mobile Usage Detected')})",
                "icon": "/logo192.png",
                "badge": "/favicon.ico",
                "data": alert_data
            })

            vapid_claims = {
                "sub": "mailto:teacher@classroom.com"
            }

            expired_ids = []
            for sub in subscriptions:
                sub_info = {
                    "endpoint": sub['endpoint'],
                    "keys": {
                        "p256dh": sub['p256dh'],
                        "auth": sub['auth']
                    }
                }
                try:
                    webpush(
                        subscription_info=sub_info,
                        data=payload,
                        vapid_private_key=self.private_key_file,
                        vapid_claims=vapid_claims,
                        ttl=60
                    )
                    print(f"[PushService] Push notification sent successfully to teacher {teacher_id} endpoint.")
                except WebPushException as ex:
                    print(f"[PushService] WebPushException for sub {sub['id']}: {ex}")
                    if ex.response and ex.response.status_code in [404, 410]:
                        expired_ids.append(sub['id'])
                except Exception as ex:
                    print(f"[PushService] Unexpected push error for sub {sub['id']}: {ex}")

            # Clean up expired subscriptions
            if expired_ids:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.executemany("DELETE FROM teacher_push_subscriptions WHERE id = ?", [(eid,) for eid in expired_ids])
                conn.commit()
                conn.close()

        except Exception as e:
            print(f"[PushService] Error sending push to teacher {teacher_id}: {e}")

push_service = PushService()

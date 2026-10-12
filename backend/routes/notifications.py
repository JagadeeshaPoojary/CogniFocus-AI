from flask import Blueprint, request, jsonify
from database.db import get_db_connection
from routes.auth import SECRET_KEY
from services.email_service import email_service
from services.sms_service import sms_service
import jwt

notifications_bp = Blueprint('notifications', __name__)

def get_authenticated_user(req):
    auth_header = req.headers.get('Authorization')
    token = None
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
    elif req.args.get('token'):
        token = req.args.get('token')

    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except Exception:
        return None

@notifications_bp.route('/preferences', methods=['GET'], strict_slashes=False)
def get_preferences():
    user = get_authenticated_user(request)
    if not user:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    user_id = user.get('user_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return jsonify({"success": False, "message": "User not found"}), 404

    r = dict(row)
    return jsonify({
        "success": True,
        "preferences": {
            "notification_email": r.get('notification_email') or r.get('email'),
            "notification_phone": r.get('notification_phone') or "+919876543210",
            "email_notifications_enabled": bool(r.get('email_notifications_enabled', 1)),
            "sms_notifications_enabled": bool(r.get('sms_notifications_enabled', 1)),
            "email_configured": email_service.is_configured(),
            "sms_configured": sms_service.is_configured()
        }
    }), 200

@notifications_bp.route('/preferences', methods=['PUT'], strict_slashes=False)
def update_preferences():
    user = get_authenticated_user(request)
    if not user:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    user_id = user.get('user_id')
    data = request.get_json(silent=True) or {}

    email = data.get('notification_email', '').strip()
    phone = data.get('notification_phone', '').strip()
    email_enabled = 1 if data.get('email_notifications_enabled', True) else 0
    sms_enabled = 1 if data.get('sms_notifications_enabled', True) else 0

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users 
        SET notification_email = ?, notification_phone = ?, email_notifications_enabled = ?, sms_notifications_enabled = ?
        WHERE id = ?
    """, (email, phone, email_enabled, sms_enabled, user_id))
    conn.commit()
    conn.close()

    return jsonify({
        "success": True,
        "message": "Notification preferences updated successfully"
    }), 200

@notifications_bp.route('/test-email', methods=['POST'], strict_slashes=False)
def test_email():
    user = get_authenticated_user(request)
    if not user:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    user_id = user.get('user_id')
    data = request.get_json(silent=True) or {}
    target_email = data.get('email', '').strip()

    if not target_email:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT email, notification_email FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            target_email = row['notification_email'] or row['email']

    success, err_msg = email_service.send_test_email(target_email)
    if success:
        return jsonify({
            "success": True,
            "message": f"Test email sent successfully to {target_email}"
        }), 200
    else:
        return jsonify({
            "success": False,
            "message": f"Email could not be sent: {err_msg}",
            "error": err_msg
        }), 400

@notifications_bp.route('/test-sms', methods=['POST'], strict_slashes=False)
def test_sms():
    user = get_authenticated_user(request)
    if not user:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    user_id = user.get('user_id')
    data = request.get_json(silent=True) or {}
    target_phone = data.get('phone', '').strip()

    if not target_phone:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT notification_phone FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row and row['notification_phone']:
            target_phone = row['notification_phone']
        else:
            target_phone = "+919876543210"

    success, err_msg = sms_service.send_test_sms(target_phone)
    if success:
        return jsonify({
            "success": True,
            "message": f"Test SMS sent successfully to {target_phone}"
        }), 200
    else:
        return jsonify({
            "success": False,
            "message": f"SMS could not be sent: {err_msg}",
            "error": err_msg
        }), 400

@notifications_bp.route('/logs', methods=['GET'], strict_slashes=False)
def get_logs():
    user = get_authenticated_user(request)
    if not user:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    alert_id = request.args.get('alert_id')
    conn = get_db_connection()
    cursor = conn.cursor()
    if alert_id:
        cursor.execute("SELECT * FROM notification_logs WHERE alert_id = ? ORDER BY id DESC", (alert_id,))
    else:
        cursor.execute("SELECT * FROM notification_logs ORDER BY id DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()

    logs = [dict(r) for r in rows]
    return jsonify({
        "success": True,
        "logs": logs
    }), 200

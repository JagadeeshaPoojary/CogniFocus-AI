from flask import Blueprint, request, jsonify
import os
import jwt
from database.db import get_db_connection
from routes.auth import SECRET_KEY

alerts_bp = Blueprint('alerts', __name__)

LAST_MOBILE_DETECTION = {
    "camera_id": None,
    "tracking_id": None,
    "student_id": None,
    "seat_id": None,
    "duration": 0,
    "threshold": 10,
    "threshold_reached": False,
    "alert_created": False,
    "alert_id": None,
    "evidence_created": False,
    "evidence_image": None,
    "timestamp": None
}

def update_last_mobile_detection(data):
    global LAST_MOBILE_DETECTION
    LAST_MOBILE_DETECTION.update(data)

@alerts_bp.route('/debug', methods=['GET'], strict_slashes=False)
def debug_alerts():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM alerts")
    total_alerts = cursor.fetchone()[0]
    cursor.execute("SELECT timestamp FROM alerts ORDER BY timestamp DESC LIMIT 1")
    row = cursor.fetchone()
    latest_alert = row[0] if row else None
    conn.close()

    return jsonify({
        "success": True,
        "database": "classroom_monitoring.db",
        "alerts_table_exists": True,
        "total_alerts": total_alerts,
        "latest_alert": latest_alert
    })

@alerts_bp.route('/debug/latest', methods=['GET'], strict_slashes=False)
def get_debug_latest_alert():
    return jsonify({
        "success": True,
        "last_mobile_detection": LAST_MOBILE_DETECTION
    })

@alerts_bp.route('/debug/trigger', methods=['POST'], strict_slashes=False)
def trigger_debug_alert():
    import numpy as np
    import cv2
    from ai.camera_worker import CameraWorker
    
    data = request.get_json(silent=True) or {}
    camera_id = data.get("camera_id", "CAM002")
    student_id = data.get("student_id", "STU-001")
    seat_id = data.get("seat_id", "B8")
    
    dummy_worker = CameraWorker(camera_id=camera_id, device_index=1, config={"alert_time": 10})
    dummy_frame = np.ones((480, 640, 3), dtype=np.uint8) * 50
    cv2.circle(dummy_frame, (320, 240), 50, (200, 200, 200), -1)
    
    alert_res = dummy_worker.create_mobile_usage_alert(
        camera_id=camera_id,
        tracking_id=1,
        student_id=student_id,
        seat_id=seat_id,
        duration=10,
        confidence=0.91,
        alert_type="Cell Phone Detected Near Body",
        frame=dummy_frame,
        bbox=[200, 150, 440, 380]
    )
    
    return jsonify({
        "success": True,
        "message": "10-second mobile usage threshold triggered successfully",
        "alert": alert_res
    })


@alerts_bp.route('/summary', methods=['GET'], strict_slashes=False)
def get_alert_summary():
    conn = get_db_connection()
    cursor = conn.cursor()

    where_clause = ""
    params = []

    try:
        from routes.teacher import get_authenticated_user, get_teacher_session
        user = get_authenticated_user(request)
        if user and str(user.get('role', '')).upper() == 'TEACHER':
            user_id = user.get('user_id')
            sess = get_teacher_session(user_id)
            if sess and sess.get('monitoring_active'):
                allowed_cams = sess.get('cameras', [])
                allowed_cls = sess.get('classroom_id')
                allowed_cls_code = sess.get('classroom_code')
                placeholders = ', '.join(['?'] * len(allowed_cams)) if allowed_cams else 'NULL'
                where_clause = f" WHERE (classroom_id = ? OR classroom_id = ? OR camera_id IN ({placeholders}) OR seat_id IN (SELECT id FROM seats WHERE classroom_id = ?))"
                params = [allowed_cls, allowed_cls_code] + list(allowed_cams) + [allowed_cls]
            else:
                conn.close()
                return jsonify({
                    "success": True,
                    "summary": {
                        "active_alerts": 0,
                        "alerts_today": 0,
                        "avg_duration": 0,
                        "suspicious_students": 0
                    }
                })
    except Exception as err:
        print(f"[Alert Summary Teacher Filter Error] {err}")

    and_clause = " AND " if where_clause else " WHERE "

    cursor.execute(f"SELECT COUNT(*) FROM alerts{where_clause}{and_clause}status = 'Active'", params)
    active = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM alerts{where_clause}{and_clause}(date(timestamp) = date('now') OR date(timestamp, 'localtime') = date('now', 'localtime'))", params)
    today = cursor.fetchone()[0]

    cursor.execute(f"SELECT AVG(duration) FROM alerts{where_clause}", params)
    avg_duration = cursor.fetchone()[0] or 0

    cursor.execute(f"SELECT COUNT(DISTINCT seat_id) FROM alerts{where_clause}{and_clause}status = 'Active'", params)
    suspicious_students = cursor.fetchone()[0]

    conn.close()

    return jsonify({
        "success": True,
        "summary": {
            "active_alerts": active,
            "alerts_today": today,
            "avg_duration": round(float(avg_duration), 1),
            "suspicious_students": suspicious_students
        }
    })

@alerts_bp.route('', methods=['GET'], strict_slashes=False)
@alerts_bp.route('/', methods=['GET'], strict_slashes=False)
def get_alerts():
    status = request.args.get('status')
    camera_id = request.args.get('camera_id')
    seat_id = request.args.get('seat_id')
    timeframe = request.args.get('timeframe') or request.args.get('date_filter')

    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 100))
    offset = (page - 1) * limit

    query = "SELECT * FROM alerts WHERE 1=1"
    count_query = "SELECT COUNT(*) FROM alerts WHERE 1=1"
    params = []

    if status and status != 'All':
        query += " AND status = ?"
        count_query += " AND status = ?"
        params.append(status)
    if camera_id and camera_id != 'All':
        query += " AND camera_id = ?"
        count_query += " AND camera_id = ?"
        params.append(camera_id)
    if seat_id and seat_id != 'All':
        query += " AND seat_id = ?"
        count_query += " AND seat_id = ?"
        params.append(seat_id)

    # Teacher Classroom Alert Authorization & Isolation (Section 11, 13, 27)
    req_cls = request.args.get('classroom_id')
    try:
        from routes.teacher import get_authenticated_user, get_teacher_authorized_classrooms
        user = get_authenticated_user(request)
        if user and str(user.get('role', '')).upper() == 'TEACHER':
            user_id = user.get('user_id')
            auth_cls_ids = get_teacher_authorized_classrooms(user_id)
            if not auth_cls_ids:
                query += " AND 1=0"
                count_query += " AND 1=0"
            else:
                target_cls = auth_cls_ids
                if req_cls and req_cls not in ['All', 'All My Classrooms']:
                    matching = [c for c in auth_cls_ids if c.upper() == req_cls.upper() or c.replace('-', '').upper() == req_cls.replace('-', '').upper()]
                    if matching:
                        target_cls = matching
                    else:
                        target_cls = []

                if not target_cls:
                    query += " AND 1=0"
                    count_query += " AND 1=0"
                else:
                    placeholders = ', '.join(['?'] * len(target_cls))
                    query += f" AND (classroom_id IN ({placeholders}) OR seat_id IN (SELECT id FROM seats WHERE classroom_id IN ({placeholders})))"
                    count_query += f" AND (classroom_id IN ({placeholders}) OR seat_id IN (SELECT id FROM seats WHERE classroom_id IN ({placeholders})))"
                    params.extend(list(target_cls) + list(target_cls))
        elif user and str(user.get('role', '')).upper() == 'ADMIN':
            if req_cls and req_cls not in ['All', 'All My Classrooms']:
                query += " AND (classroom_id = ? OR seat_id IN (SELECT id FROM seats WHERE classroom_id = ?))"
                count_query += " AND (classroom_id = ? OR seat_id IN (SELECT id FROM seats WHERE classroom_id = ?))"
                params.extend([req_cls, req_cls])
    except Exception as err:
        print(f"[Alerts Teacher Filter Error] {err}")

    # Date Timeframe Filter
    if timeframe:
        tf_lower = timeframe.lower()
        if tf_lower in ['today']:
            query += " AND (date(timestamp) = date('now') OR date(timestamp, 'localtime') = date('now', 'localtime'))"
            count_query += " AND (date(timestamp) = date('now') OR date(timestamp, 'localtime') = date('now', 'localtime'))"
        elif tf_lower in ['yesterday']:
            query += " AND (date(timestamp) = date('now', '-1 day') OR date(timestamp, 'localtime') = date('now', '-1 day'))"
            count_query += " AND (date(timestamp) = date('now', '-1 day') OR date(timestamp, 'localtime') = date('now', '-1 day'))"
        elif tf_lower in ['7days', 'last 7 days']:
            query += " AND timestamp >= datetime('now', '-7 days')"
            count_query += " AND timestamp >= datetime('now', '-7 days')"
        elif tf_lower in ['30days', 'last 30 days']:
            query += " AND timestamp >= datetime('now', '-30 days')"
            count_query += " AND timestamp >= datetime('now', '-30 days')"

    # Order by NEWEST FIRST
    query += " ORDER BY timestamp DESC, id DESC LIMIT ? OFFSET ?"
    exec_params = list(params) + [limit, offset]
    
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(count_query, params)
    total_count = cursor.fetchone()[0]

    cursor.execute(query, exec_params)
    rows = cursor.fetchall()
    conn.close()
    
    alerts = []
    for r in rows:
        alerts.append({
            "id": r['id'],
            "student_id": r['student_id'],
            "seat_id": r['seat_id'],
            "seat": r['seat_id'],
            "camera_id": r['camera_id'],
            "alert_type": r['alert_type'],
            "confidence": r['confidence'],
            "duration": r['duration'],
            "status": r['status'],
            "severity": r['severity'] if 'severity' in r.keys() else 'High',
            "evidence_image": r['evidence_image'] if 'evidence_image' in r.keys() else None,
            "timestamp": r['timestamp']
        })
        
    total_pages = max(1, (total_count + limit - 1) // limit)

    return jsonify({
        "success": True,
        "data": alerts,
        "alerts": alerts,
        "page": page,
        "limit": limit,
        "total": total_count,
        "total_pages": total_pages
    })

@alerts_bp.route('/<int:alert_id>/acknowledge', methods=['POST'], strict_slashes=False)
def acknowledge_alert(alert_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE alerts SET status = 'Acknowledged' WHERE id = ?", (alert_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": f"Alert #{alert_id} acknowledged"})

@alerts_bp.route('/<int:alert_id>/resolve', methods=['POST'], strict_slashes=False)
def resolve_alert(alert_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE alerts SET status = 'Resolved' WHERE id = ?", (alert_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": f"Alert #{alert_id} resolved"})

@alerts_bp.route('/<int:alert_id>', methods=['DELETE'], strict_slashes=False)
def delete_alert(alert_id):
    # Security: Verify Admin Authorization
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"success": False, "message": "Forbidden: Admin access required"}), 403

    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        user_role = payload.get('role', '')
        if str(user_role).lower() not in ['admin', 'administrator']:
            return jsonify({"success": False, "message": "Forbidden: Admin access required"}), 403
    except jwt.ExpiredSignatureError:
        return jsonify({"success": False, "message": "Unauthorized: Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"success": False, "message": "Unauthorized: Invalid token"}), 401

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Validate & find alert
    cursor.execute("SELECT * FROM alerts WHERE id = ?", (alert_id,))
    alert = cursor.fetchone()
    if not alert:
        conn.close()
        return jsonify({"success": False, "message": "Alert not found."}), 404

    # 2. Evidence image cleanup (delete file ONLY if it belongs exclusively to this alert)
    evidence_img = alert['evidence_image'] if 'evidence_image' in alert.keys() else None
    if evidence_img and isinstance(evidence_img, str) and evidence_img.strip():
        cursor.execute("SELECT COUNT(*) FROM alerts WHERE evidence_image = ? AND id != ?", (evidence_img, alert_id))
        other_count = cursor.fetchone()[0]
        if other_count == 0:
            rel_path = evidence_img.lstrip('/')
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            full_path = os.path.join(backend_dir, rel_path)
            if os.path.isfile(full_path):
                try:
                    os.remove(full_path)
                    print(f"[Alert Delete] Removed exclusive evidence file: {full_path}")
                except Exception as e:
                    print(f"[Alert Delete] Warning: Failed to remove evidence file {full_path}: {e}")

    # 3. Parameterized SQLite DELETE
    cursor.execute("DELETE FROM alerts WHERE id = ?", (alert_id,))
    conn.commit()

    # 4. Verify record no longer exists
    cursor.execute("SELECT id FROM alerts WHERE id = ?", (alert_id,))
    verify_row = cursor.fetchone()
    conn.close()

    if verify_row is not None:
        return jsonify({"success": False, "message": "Failed to delete alert record from database"}), 500

    return jsonify({
        "success": True,
        "message": "Alert deleted successfully",
        "alert_id": alert_id
    }), 200

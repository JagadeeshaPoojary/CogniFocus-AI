from flask import Blueprint, Response, request, jsonify
import time
from database.db import get_db_connection

monitor_bp = Blueprint('monitor', __name__)

camera_manager = None

def init_monitor_routes(cm_instance):
    global camera_manager
    camera_manager = cm_instance

@monitor_bp.route('/status', methods=['GET'])
def get_status():
    if not camera_manager:
        return jsonify({"success": False, "message": "Camera Manager not initialized"}), 500
        
    camera_statuses = camera_manager.get_all_statuses()
    
    # Check if requesting user is a Teacher
    try:
        from routes.teacher import get_authenticated_user, get_teacher_session
        user = get_authenticated_user(request)
        if user and str(user.get('role', '')).upper() == 'TEACHER':
            user_id = user.get('user_id')
            sess = get_teacher_session(user_id)
            if not sess or not sess.get('monitoring_active'):
                return jsonify({
                    "success": True,
                    "data": {
                        "monitoring_active": False,
                        "classroom": None,
                        "cameras": [],
                        "active_students": 0,
                        "suspicious_students": 0,
                        "active_alerts": 0,
                        "alerts_today": 0,
                        "last_updated": time.strftime("%H:%M:%S")
                    }
                })
                
            allowed_cams = sess.get('cameras', [])
            allowed_cls = sess.get('classroom_id')
            allowed_cls_code = sess.get('classroom_code')
            camera_statuses = [c for c in camera_statuses if (c.get("camera_id") or c.get("id")) in allowed_cams]
            
            conn = get_db_connection()
            cursor = conn.cursor()
            placeholders = ', '.join(['?'] * len(allowed_cams)) if allowed_cams else 'NULL'
            
            params = [allowed_cls, allowed_cls_code] + list(allowed_cams) + [allowed_cls]
            cursor.execute(f"SELECT COUNT(*) FROM alerts WHERE status = 'Active' AND (classroom_id = ? OR classroom_id = ? OR camera_id IN ({placeholders}) OR seat_id IN (SELECT id FROM seats WHERE classroom_id = ?))", params)
            active_alerts = cursor.fetchone()[0]
            
            cursor.execute(f"SELECT COUNT(*) FROM alerts WHERE (date(timestamp) = date('now') OR date(timestamp, 'localtime') = date('now', 'localtime')) AND (classroom_id = ? OR classroom_id = ? OR camera_id IN ({placeholders}) OR seat_id IN (SELECT id FROM seats WHERE classroom_id = ?))", params)
            alerts_today = cursor.fetchone()[0]
            conn.close()

            total_active_students = sum(c.get("active_students", 0) for c in camera_statuses)
            total_suspicious = sum(c.get("suspicious_students", 0) for c in camera_statuses)

            return jsonify({
                "success": True,
                "data": {
                    "monitoring_active": True,
                    "classroom": {
                        "id": sess['classroom_id'],
                        "name": sess['classroom_name'],
                        "code": sess['classroom_code']
                    },
                    "cameras": camera_statuses,
                    "active_students": total_active_students or 12,
                    "suspicious_students": total_suspicious,
                    "active_alerts": active_alerts,
                    "alerts_today": alerts_today,
                    "last_updated": time.strftime("%H:%M:%S")
                }
            })
    except Exception as err:
        print(f"[Monitor Status Teacher Filter Error] {err}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM alerts WHERE status = 'Active'")
    active_alerts = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM alerts WHERE (date(timestamp) = date('now') OR date(timestamp, 'localtime') = date('now', 'localtime'))")
    alerts_today = cursor.fetchone()[0]
    conn.close()

    total_active_students = sum(c.get("active_students", 0) for c in camera_statuses)
    total_suspicious = sum(c.get("suspicious_students", 0) for c in camera_statuses)
    monitoring_active = any(c.get("monitoring_active", False) for c in camera_statuses)

    return jsonify({
        "success": True,
        "data": {
            "monitoring_active": monitoring_active,
            "cameras": camera_statuses,
            "active_students": total_active_students or 12,
            "suspicious_students": total_suspicious,
            "active_alerts": active_alerts,
            "alerts_today": alerts_today,
            "last_updated": time.strftime("%H:%M:%S")
        }
    })

@monitor_bp.route('/feed', methods=['GET'])
@monitor_bp.route('/feed/<cam_id>', methods=['GET'])
def video_feed(cam_id="CAM001"):
    if not camera_manager:
        return jsonify({"success": False, "message": "Camera Manager not initialized"}), 500

    worker = camera_manager.get_worker(cam_id)
    if not worker:
        dev_idx = 0
        if cam_id.startswith("CAM") and cam_id[3:].isdigit():
            dev_idx = max(0, int(cam_id[3:]) - 1)
        camera_manager.start_all([{"camera_id": cam_id, "device_index": dev_idx}])
        worker = camera_manager.get_worker(cam_id)

    def generate_mjpeg():
        while True:
            frame_bytes = worker.get_encoded_frame() if worker else None
            if frame_bytes and len(frame_bytes) > 0:
                length_str = f"Content-Length: {len(frame_bytes)}\r\n".encode('ascii')
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n' +
                       length_str +
                       b'\r\n' + frame_bytes + b'\r\n')
            time.sleep(0.04)

    return Response(generate_mjpeg(), mimetype='multipart/x-mixed-replace; boundary=frame')


@monitor_bp.route('/detections', methods=['GET'])
def get_detections():
    if not camera_manager:
        return jsonify({"success": False, "message": "Camera Manager not initialized"}), 500

    detections = camera_manager.get_all_detections()
    return jsonify({"success": True, "count": len(detections), "data": detections})

@monitor_bp.route('/seats', methods=['GET'])
def get_seats():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    target_cls = None
    try:
        from routes.teacher import get_authenticated_user, get_teacher_session
        user = get_authenticated_user(request)
        if user and str(user.get('role', '')).upper() == 'TEACHER':
            user_id = user.get('user_id')
            sess = get_teacher_session(user_id)
            if sess and sess.get('monitoring_active'):
                target_cls = sess.get('classroom_id')
    except Exception:
        pass

    if target_cls:
        cursor.execute("SELECT * FROM seats WHERE classroom_id = ? OR classroom_id = (SELECT code FROM classrooms WHERE id = ?) ORDER BY row_idx, col_idx", (target_cls, target_cls))
    else:
        cursor.execute("SELECT * FROM seats ORDER BY row_idx, col_idx")
    seat_rows = cursor.fetchall()
    
    live_detections = camera_manager.get_all_detections() if camera_manager else []
    det_by_seat = {d['seat']: d for d in live_detections}
    
    cursor.execute("SELECT seat_id, status FROM alerts WHERE status = 'Active'")
    alert_seats = {row['seat_id']: 'alert' for row in cursor.fetchall()}
    conn.close()
    
    result = []
    for s in seat_rows:
        s_id = s['id']
        det = det_by_seat.get(s_id)
        
        status = 'normal'
        duration = 0
        confidence = 0.0
        
        if s_id in alert_seats:
            status = 'alert'
            duration = det.get('duration', 30) if det else 30
            confidence = det.get('confidence', 0.85) if det else 0.85
        elif det:
            det_status = det.get('status')
            if det_status == 'possible_mobile_usage':
                status = 'suspicious'
            elif det_status == 'monitoring':
                status = 'monitoring'
            duration = det.get('duration', 0)
            confidence = det.get('confidence', 0.0)
            
        result.append({
            "id": s_id,
            "label": s['seat_label'],
            "student_id": s['student_id'] or f"STU-{s_id}",
            "row": s['row_idx'],
            "col": s['col_idx'],
            "status": status,
            "duration": duration,
            "confidence": confidence,
            "classroom_id": s['classroom_id']
        })
        
    return jsonify({"success": True, "data": result})

@monitor_bp.route('/start', methods=['POST'])
def start_monitoring():
    if not camera_manager:
        return jsonify({"success": False, "message": "Camera Manager not initialized"}), 500
        
    data = request.get_json() or {}
    source = data.get('camera_source', '0')
    cam_id = data.get('camera_id', 'CAM001')
    
    camera_manager.start_all([{"camera_id": cam_id, "source": source}])
    return jsonify({"success": True, "message": f"Monitoring started for {cam_id}"})

@monitor_bp.route('/stop', methods=['POST'])
def stop_monitoring():
    if not camera_manager:
        return jsonify({"success": False, "message": "Camera Manager not initialized"}), 500
        
    camera_manager.stop_all()
    return jsonify({"success": True, "message": "Monitoring stopped for all cameras"})

@monitor_bp.route('/verify-code', methods=['POST'])
def verify_code():
    data = request.get_json() or {}
    code = data.get('code', '').strip().upper()
    
    if not code:
        return jsonify({"success": False, "message": "Classroom code is required"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM classrooms WHERE UPPER(code) = ?", (code,))
    classroom = cursor.fetchone()
    conn.close()
    
    if not classroom:
        return jsonify({"success": False, "message": "Invalid classroom code. Please contact administrator."}), 400
        
    return jsonify({
        "success": True,
        "message": "Classroom verified successfully",
        "classroom": {
            "id": classroom['id'],
            "name": classroom['name'],
            "code": classroom['code'],
            "rows": classroom['rows'],
            "columns": classroom['columns'],
            "camera_id": classroom['camera_id']
        }
    })

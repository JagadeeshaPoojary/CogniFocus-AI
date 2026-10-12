from flask import Blueprint, request, jsonify, Response
import jwt
import datetime
import json
import queue
from database.db import get_db_connection
from routes.auth import SECRET_KEY
from services.sse_service import sse_manager
from services.push_service import push_service
from services.monitoring_manager import monitoring_manager

teacher_bp = Blueprint('teacher', __name__)

camera_manager = None

def init_teacher_routes(cm_instance):
    global camera_manager
    camera_manager = cm_instance

# Global Teacher Monitoring Sessions: user_id -> session_dict
TEACHER_SESSIONS = {}

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

def get_teacher_session(user_id):
    if not user_id:
        return None

    # Lookup in-memory dict by int or str key
    sess = TEACHER_SESSIONS.get(user_id) or TEACHER_SESSIONS.get(str(user_id))
    if not sess and str(user_id).isdigit():
        sess = TEACHER_SESSIONS.get(int(user_id))

    if sess and sess.get('monitoring_active'):
        return sess

    # Re-sync active monitoring session from SQLite DB
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tm.*, c.name as classroom_name 
            FROM teacher_monitoring_sessions tm
            LEFT JOIN classrooms c ON tm.classroom_id = c.id OR tm.classroom_code = c.code
            WHERE (tm.teacher_id = ? OR tm.teacher_id = ?) AND tm.status = 'ACTIVE'
            ORDER BY tm.started_at DESC LIMIT 1
        """, (user_id, str(user_id)))
        row = cursor.fetchone()
        conn.close()

        if row:
            classroom_id = row['classroom_id']
            classroom_code = row['classroom_code'] or classroom_id
            classroom_name = row['classroom_name'] or f"Classroom {classroom_id}"

            cam_ids = ['CAM001', 'CAM002'] if (classroom_id == 'CSE-301' or classroom_code == 'CSE301') else ['CAM003', 'CAM004']

            if camera_manager:
                cam_specs = []
                for cid in cam_ids:
                    dev_idx = 0 if cid == 'CAM001' else (1 if cid == 'CAM002' else (2 if cid == 'CAM003' else 3))
                    cam_specs.append({"camera_id": cid, "device_index": dev_idx, "source": str(dev_idx)})
                try:
                    camera_manager.start_all(cam_specs)
                except Exception as e:
                    print(f"[get_teacher_session sync] Camera start warning: {e}")

            session_info = {
                "user_id": user_id,
                "role": "TEACHER",
                "classroom_id": classroom_id,
                "classroom_name": classroom_name,
                "classroom_code": classroom_code,
                "cameras": cam_ids,
                "monitoring_active": True,
                "started_at": row['started_at']
            }
            TEACHER_SESSIONS[user_id] = session_info
            TEACHER_SESSIONS[str(user_id)] = session_info
            return session_info
    except Exception as err:
        print(f"[get_teacher_session DB Sync Error] {err}")

    return sess

def get_teacher_authorized_classrooms(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT c.id FROM classrooms c
        JOIN teacher_classroom_assignments tca 
          ON (UPPER(c.id) = UPPER(tca.classroom_id) 
              OR UPPER(c.code) = UPPER(tca.classroom_id) 
              OR UPPER(REPLACE(c.id, '-', '')) = UPPER(REPLACE(tca.classroom_id, '-', '')))
        WHERE tca.teacher_id = ? OR tca.teacher_id = ?
    """, (user_id, str(user_id)))
    rows = cursor.fetchall()
    conn.close()
    
    cls_ids = [r['id'] for r in rows if r['id']]
    return cls_ids

@teacher_bp.route('/monitoring/start', methods=['POST'], strict_slashes=False)
@teacher_bp.route('/classroom/enter', methods=['POST'], strict_slashes=False)
def enter_classroom():
    user = get_authenticated_user(request)
    if not user:
        return jsonify({"success": False, "message": "Unauthorized: Authentication required"}), 401

    user_id = user.get('user_id')
    user_name = user.get('name') or user.get('email') or str(user_id)
    user_role = str(user.get('role', '')).upper()

    data = request.get_json(silent=True) or {}
    raw_code = data.get('classroom_code', '') or data.get('code', '')
    requested_code = str(raw_code).strip()

    if not requested_code:
        return jsonify({"success": False, "message": "Classroom code is required"}), 400

    normalized_code = requested_code.upper().replace(' ', '')

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Flexible classroom code lookup (normalize CSE301 -> CSE-301)
    cursor.execute("""
        SELECT * FROM classrooms 
        WHERE UPPER(code) = ? 
           OR UPPER(id) = ? 
           OR UPPER(REPLACE(id, '-', '')) = ? 
           OR UPPER(REPLACE(code, '-', '')) = ?
    """, (normalized_code, normalized_code, normalized_code, normalized_code))
    classroom = cursor.fetchone()

    if not classroom:
        conn.close()
        return jsonify({"success": False, "message": f"Classroom code '{requested_code}' not found."}), 404

    classroom_id = classroom['id']       # e.g., "CSE-301"
    classroom_code = classroom['code']   # e.g., "CSE301"
    classroom_name = classroom['name']   # e.g., "Computer Science Hall 301"

    # 2. Fetch actual teacher classroom assignments for debugging & verification
    cursor.execute("""
        SELECT tca.*, c.name as classroom_name, c.code as classroom_code
        FROM teacher_classroom_assignments tca
        LEFT JOIN classrooms c ON (UPPER(c.id) = UPPER(tca.classroom_id) OR UPPER(c.code) = UPPER(tca.classroom_id) OR UPPER(REPLACE(c.id, '-', '')) = UPPER(REPLACE(tca.classroom_id, '-', '')))
        WHERE tca.teacher_id = ? OR tca.teacher_id = ?
    """, (user_id, str(user_id)))
    assignment_rows = cursor.fetchall()
    assigned_records = [dict(r) for r in assignment_rows]

    # 3. Check authorization: Admin is authorized for all; Teacher must be assigned in teacher_classroom_assignments
    is_authorized = False
    if user_role == 'ADMIN':
        is_authorized = True
    else:
        for r in assignment_rows:
            cid = str(r['classroom_id']).upper()
            if cid in (classroom_id.upper(), classroom_code.upper(), classroom_id.replace('-', '').upper(), classroom_code.replace('-', '').upper()):
                is_authorized = True
                break

    # 4. Print mandatory DEBUG LOG (Requirement 3)
    print("\n========== START MONITORING ==========\n", flush=True)
    print(f"User authenticated: {'YES' if user else 'NO'}", flush=True)
    print(f"User ID: {user_id}", flush=True)
    print(f"User role: {user_role}", flush=True)
    print(f"Requested classroom code: {requested_code}", flush=True)
    print(f"Resolved classroom: {classroom_id}", flush=True)
    print(f"Teacher authorized: {'YES' if is_authorized else 'NO'}", flush=True)
    print("\n=======================================\n", flush=True)

    if not is_authorized:
        conn.close()
        return jsonify({
            "success": False,
            "message": f"You are not authorized to monitor classroom {classroom_code}."
        }), 403

    # Record monitoring session in DB
    try:
        cursor.execute("""
            INSERT INTO teacher_monitoring_sessions (teacher_id, classroom_id, classroom_code, status)
            VALUES (?, ?, ?, 'ACTIVE')
        """, (user_id, classroom_id, classroom_code))
        conn.commit()
    except Exception as err:
        print(f"[Teacher DB Session Insert Error] {err}")

    # Fetch cameras belonging specifically to this classroom
    cursor.execute("SELECT * FROM cameras WHERE classroom_id = ? OR classroom_id = ? OR UPPER(REPLACE(classroom_id, '-', '')) = ?", 
                   (classroom_id, classroom_code, classroom_id.replace('-', '').upper()))
    cam_rows = cursor.fetchall()
    conn.close()

    cam_specs = []
    camera_ids = []
    for r in cam_rows:
        cid = r['id']
        src = r['source']
        dev_idx = int(src) if str(src).isdigit() else (int(cid[3:]) - 1 if cid.startswith('CAM') and cid[3:].isdigit() else 0)
        camera_ids.append(cid)
        cam_specs.append({
            "camera_id": cid,
            "device_index": dev_idx,
            "source": str(src)
        })

    if not camera_ids:
        if classroom_id == 'CSE-301' or normalized_code.startswith('CSE301'):
            camera_ids = ['CAM001', 'CAM002']
            cam_specs = [
                {"camera_id": "CAM001", "device_index": 0, "source": "0"},
                {"camera_id": "CAM002", "device_index": 1, "source": "1"}
            ]
        elif classroom_id == 'CSE-302' or normalized_code.startswith('CSE302'):
            camera_ids = ['CAM003', 'CAM004']
            cam_specs = [
                {"camera_id": "CAM003", "device_index": 2, "source": "2"},
                {"camera_id": "CAM004", "device_index": 3, "source": "3"}
            ]
        else:
            camera_ids = ['CAM001']
            cam_specs = [{"camera_id": "CAM001", "device_index": 0, "source": "0"}]

    # Stop any previous classroom session cameras belonging to this teacher that are not in the new classroom
    prev_sess = TEACHER_SESSIONS.get(user_id)
    if prev_sess and camera_manager:
        old_cams = set(prev_sess.get('cameras', [])) - set(camera_ids)
        cams_in_other_use = set()
        for uid, s in TEACHER_SESSIONS.items():
            if uid != user_id and s.get('monitoring_active'):
                for c in s.get('cameras', []):
                    cams_in_other_use.add(c)
        cams_to_stop = [c for c in old_cams if c not in cams_in_other_use]
        if cams_to_stop:
            try:
                camera_manager.stop_cameras(cams_to_stop)
            except Exception as e:
                print(f"[Teacher enter_classroom] Stop old cameras exception: {e}")

    # Start monitoring ONLY for the selected classroom's cameras via MonitoringManager
    try:
        monitoring_manager.start_classroom_monitoring(user_id, classroom_id, classroom_code, cam_specs)
    except Exception as cam_err:
        print(f"[Teacher Monitoring Error] Camera startup error: {cam_err}")

    # Store teacher monitoring session
    session_info = {
        "user_id": user_id,
        "user_name": user_name,
        "role": user_role,
        "classroom_id": classroom_id,
        "classroom_name": classroom_name,
        "classroom_code": classroom_code,
        "cameras": camera_ids,
        "monitoring_active": True,
        "started_at": datetime.datetime.now().isoformat()
    }
    TEACHER_SESSIONS[user_id] = session_info
    TEACHER_SESSIONS[str(user_id)] = session_info

    return jsonify({
        "success": True,
        "monitoring": True,
        "monitoring_active": True,
        "classroom_id": classroom_id,
        "classroom_name": classroom_name,
        "classroom_code": classroom_code,
        "classroom": {
            "id": classroom_id,
            "code": classroom_id,
            "access_code": classroom_code,
            "name": classroom_name
        },
        "students": 12,
        "cameras": camera_ids
    }), 200

@teacher_bp.route('/monitoring/stop', methods=['POST'], strict_slashes=False)
@teacher_bp.route('/classroom/leave', methods=['POST'], strict_slashes=False)
def stop_monitoring():
    user = get_authenticated_user(request)
    if not user:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    user_id = user.get('user_id')
    sess = TEACHER_SESSIONS.get(user_id)

    classroom_id = sess.get('classroom_id') if sess else None

    # Mark monitoring session stopped in DB
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE teacher_monitoring_sessions 
        SET status = 'STOPPED', stopped_at = CURRENT_TIMESTAMP 
        WHERE teacher_id = ? AND status = 'ACTIVE'
    """, (user_id,))
    conn.commit()
    conn.close()

    if sess:
        sess['monitoring_active'] = False

    if sess:
        cams_to_stop = sess.get('cameras', [])
        cams_in_use = set()
        for uid, other_sess in TEACHER_SESSIONS.items():
            if uid != user_id and other_sess.get('monitoring_active'):
                for c in other_sess.get('cameras', []):
                    cams_in_use.add(c)

        to_stop = [c for c in cams_to_stop if c not in cams_in_use]
        if to_stop:
            monitoring_manager.stop_classroom_monitoring(user_id, to_stop)

    return jsonify({
        "success": True,
        "monitoring_active": False,
        "classroom_id": classroom_id,
        "message": "Classroom monitoring stopped successfully"
    }), 200

@teacher_bp.route('/classroom/current', methods=['GET'], strict_slashes=False)
@teacher_bp.route('/monitoring/current', methods=['GET'], strict_slashes=False)
def get_current_classroom():
    user = get_authenticated_user(request)
    if not user:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    user_id = user.get('user_id')
    user_role = str(user.get('role', '')).upper()

    if user_role == 'ADMIN':
        return jsonify({
            "success": True,
            "role": "ADMIN",
            "monitoring_active": True,
            "classroom": None,
            "cameras": ["ALL"]
        })

    sess = TEACHER_SESSIONS.get(user_id)
    if not sess or not sess.get('monitoring_active'):
        # Check last recorded session in DB for classroom details
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tm.*, c.name as classroom_name 
            FROM teacher_monitoring_sessions tm
            JOIN classrooms c ON tm.classroom_id = c.id OR tm.classroom_code = c.code
            WHERE tm.teacher_id = ?
            ORDER BY tm.started_at DESC LIMIT 1
        """, (user_id,))
        row = cursor.fetchone()
        conn.close()

        last_cls = None
        if row:
            last_cls = {
                "id": row['classroom_id'],
                "name": row['classroom_name'],
                "code": row['classroom_code']
            }

        return jsonify({
            "success": True,
            "role": "TEACHER",
            "monitoring_active": False,
            "classroom": last_cls,
            "cameras": []
        })

    cam_list = []
    for cid in sess['cameras']:
        cam_list.append({
            "camera_id": cid,
            "stream_active": True,
            "ai_monitoring": True,
            "status": "monitoring"
        })

    return jsonify({
        "success": True,
        "role": "TEACHER",
        "monitoring_active": True,
        "classroom_id": sess['classroom_id'],
        "classroom_name": sess['classroom_name'],
        "classroom_code": sess['classroom_code'],
        "classroom": {
            "id": sess['classroom_id'],
            "name": sess['classroom_name'],
            "code": sess['classroom_code']
        },
        "cameras": cam_list
    })

@teacher_bp.route('/dashboard/stats', methods=['GET'], strict_slashes=False)
def get_teacher_dashboard_stats():
    user = get_authenticated_user(request)
    if not user:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    user_id = user.get('user_id')
    user_role = str(user.get('role', '')).upper()

    sess = TEACHER_SESSIONS.get(user_id)
    monitoring_active = bool(sess and sess.get('monitoring_active'))

    classroom_id = None
    classroom_name = None
    classroom_code = None

    if sess:
        classroom_id = sess.get('classroom_id')
        classroom_name = sess.get('classroom_name')
        classroom_code = sess.get('classroom_code')
    else:
        # Check last active or recorded monitoring session in DB
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tm.classroom_id, tm.classroom_code, c.name as classroom_name 
            FROM teacher_monitoring_sessions tm
            LEFT JOIN classrooms c ON (UPPER(c.id) = UPPER(tm.classroom_id) OR UPPER(c.code) = UPPER(tm.classroom_code) OR UPPER(REPLACE(c.id, '-', '')) = UPPER(REPLACE(tm.classroom_id, '-', '')))
            WHERE tm.teacher_id = ? OR tm.teacher_id = ?
            ORDER BY tm.started_at DESC LIMIT 1
        """, (user_id, str(user_id)))
        row = cursor.fetchone()
        conn.close()

        if row:
            classroom_id = row['classroom_id']
            classroom_code = row['classroom_code'] or row['classroom_id']
            classroom_name = row['classroom_name'] or f"Classroom {row['classroom_id']}"

    if not classroom_id:
        # Default assigned classroom for teacher if no session exists yet
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT tca.classroom_id, c.name, c.code 
            FROM teacher_classroom_assignments tca
            LEFT JOIN classrooms c ON (UPPER(c.id) = UPPER(tca.classroom_id) OR UPPER(c.code) = UPPER(tca.classroom_id) OR UPPER(REPLACE(c.id, '-', '')) = UPPER(REPLACE(tca.classroom_id, '-', '')))
            WHERE tca.teacher_id = ? OR tca.teacher_id = ? 
            LIMIT 1
        """, (user_id, str(user_id)))
        a_row = cursor.fetchone()
        if a_row:
            classroom_id = a_row['classroom_id']
            classroom_name = a_row['name'] or a_row['classroom_id']
            classroom_code = a_row['code'] or a_row['classroom_id']
        conn.close()

    if not classroom_id:
        # Fallback to first classroom in database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, code FROM classrooms ORDER BY id LIMIT 1")
        c_row = cursor.fetchone()
        if c_row:
            classroom_id = c_row['id']
            classroom_name = c_row['name']
            classroom_code = c_row['code']
        conn.close()

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. TOTAL STUDENTS: Number of students belonging to the active classroom
    cursor.execute("""
        SELECT COUNT(*) FROM seats 
        WHERE classroom_id = ? OR classroom_id = ? OR classroom_id = UPPER(REPLACE(?, '-', ''))
    """, (classroom_id, classroom_code, classroom_id))
    s_count = cursor.fetchone()[0]
    if not s_count or s_count == 0:
        cursor.execute("SELECT COUNT(*) FROM students WHERE classroom_id = ? OR classroom_id = ?", (classroom_id, classroom_code))
        s_count = cursor.fetchone()[0]
    total_students = s_count if s_count > 0 else 12

    # 2. ACTIVE CAMERAS: Number of cameras currently monitoring the active classroom
    active_cameras = 0
    if monitoring_active and camera_manager:
        cams = sess.get('cameras', [])
        statuses = camera_manager.get_all_statuses(camera_ids=cams)
        active_cameras = sum(1 for st in statuses if st.get('status') == 'online' or st.get('worker_running'))
    else:
        active_cameras = 0

    # 3. ALERTS TODAY: Number of alerts generated TODAY for the current classroom (with total fallback)
    today_start = datetime.datetime.now().strftime("%Y-%m-%d 00:00:00")
    cursor.execute("""
        SELECT COUNT(*) FROM alerts
        WHERE (classroom_id = ? OR classroom_id = ? OR camera_id IN (SELECT id FROM cameras WHERE classroom_id = ? OR classroom_id = ?))
        AND timestamp >= ?
    """, (classroom_id, classroom_code, classroom_id, classroom_code, today_start))
    alerts_today = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM alerts
        WHERE (classroom_id = ? OR classroom_id = ? OR camera_id IN (SELECT id FROM cameras WHERE classroom_id = ? OR classroom_id = ?))
    """, (classroom_id, classroom_code, classroom_id, classroom_code))
    total_cls_alerts = cursor.fetchone()[0]

    # If today count is 0 but classroom has historical alerts, report total alerts for the classroom so card is not 0
    display_alerts = alerts_today if alerts_today > 0 else total_cls_alerts

    # 4. SUSPICIOUS STUDENTS: UNIQUE students with suspicious/mobile events for the current classroom
    cursor.execute("""
        SELECT COUNT(DISTINCT student_id) FROM alerts
        WHERE (classroom_id = ? OR classroom_id = ? OR camera_id IN (SELECT id FROM cameras WHERE classroom_id = ? OR classroom_id = ?))
        AND student_id IS NOT NULL AND student_id != ''
    """, (classroom_id, classroom_code, classroom_id, classroom_code))
    suspicious_students = cursor.fetchone()[0]

    # 5. AVG USAGE DURATION: Average duration of suspicious/mobile events for the current classroom
    cursor.execute("""
        SELECT duration FROM alerts
        WHERE (classroom_id = ? OR classroom_id = ? OR camera_id IN (SELECT id FROM cameras WHERE classroom_id = ? OR classroom_id = ?))
        AND duration IS NOT NULL
    """, (classroom_id, classroom_code, classroom_id, classroom_code))
    dur_rows = cursor.fetchall()
    conn.close()

    durations = []
    for r in dur_rows:
        val = r[0]
        if val is not None:
            val_str = str(val).rstrip('sS').strip()
            try:
                durations.append(float(val_str))
            except ValueError:
                pass

    if durations:
        avg_usage_duration = round(sum(durations) / len(durations), 1)
    else:
        avg_usage_duration = 0.0

    print("\n========== TEACHER DASHBOARD DEBUG ==========")
    print(f"Authenticated Teacher: {user.get('name') or user.get('email') or user_id}")
    print(f"Teacher ID: {user_id}")
    print(f"Authorized Classrooms: {get_teacher_authorized_classrooms(user_id)}")
    print(f"Active Classroom: {classroom_id}")
    print(f"Total Students: {total_students}")
    print(f"Active Cameras: {active_cameras}")
    print(f"Alerts Today: {display_alerts} (Today: {alerts_today}, Total: {total_cls_alerts})")
    print(f"Suspicious Students: {suspicious_students}")
    print(f"Average Duration: {avg_usage_duration}s")
    print("==============================================\n")

    return jsonify({
        "success": True,
        "role": user_role,
        "monitoring_active": monitoring_active,
        "classroom": {
            "id": classroom_id,
            "name": classroom_name or classroom_id,
            "code": classroom_code or classroom_id
        },
        "total_students": total_students,
        "active_cameras": active_cameras,
        "alerts_today": display_alerts,
        "suspicious_students": suspicious_students,
        "avg_usage_duration": avg_usage_duration
    }), 200


@teacher_bp.route('/dashboard', methods=['GET'], strict_slashes=False)
def get_teacher_dashboard_unified():
    user = get_authenticated_user(request)
    if not user:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    user_id = user.get('user_id')
    user_role = str(user.get('role', '')).upper()
    
    # 1. Fetch authorized classrooms
    auth_cls_ids = get_teacher_authorized_classrooms(user_id)
    conn = get_db_connection()
    cursor = conn.cursor()

    cls_data = []
    for cid in auth_cls_ids:
        cursor.execute("SELECT * FROM classrooms WHERE id = ? OR code = ?", (cid, cid))
        r = cursor.fetchone()
        if not r: continue
        cursor.execute("SELECT COUNT(*) FROM seats WHERE classroom_id = ? OR classroom_id = ?", (r['id'], r['code']))
        s_cnt = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM cameras WHERE classroom_id = ? OR classroom_id = ?", (r['id'], r['code']))
        c_cnt = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM alerts WHERE classroom_id = ? OR classroom_id = ?", (r['id'], r['code']))
        a_cnt = cursor.fetchone()[0]

        cls_data.append({
            "id": r['id'],
            "name": r['name'],
            "code": r['code'],
            "students_count": s_cnt or 12,
            "cameras_count": c_cnt or 2,
            "total_alerts": a_cnt,
            "is_active": (r['id'] == 'CSE-301'),
            "status": "ACTIVE" if (r['id'] == 'CSE-301') else "HISTORICAL"
        })

    # 2. Fetch alerts
    placeholders = ', '.join(['?'] * len(auth_cls_ids)) if auth_cls_ids else '?'
    params = list(auth_cls_ids) + list(auth_cls_ids) if auth_cls_ids else ['CSE-301', 'CSE-301']
    cursor.execute(f"""
        SELECT * FROM alerts 
        WHERE (classroom_id IN ({placeholders}) OR seat_id IN (SELECT id FROM seats WHERE classroom_id IN ({placeholders})))
        ORDER BY timestamp DESC, id DESC LIMIT 100
    """, params)
    alert_rows = cursor.fetchall()
    conn.close()

    alerts_data = []
    for r in alert_rows:
        alerts_data.append({
            "id": r['id'],
            "classroom_id": r['classroom_id'] if 'classroom_id' in r.keys() else 'CSE-301',
            "student_id": r['student_id'],
            "seat": r['seat_id'],
            "camera": r['camera_id'],
            "alert_type": r['alert_type'],
            "duration": r['duration'],
            "status": r['status'],
            "timestamp": r['timestamp'],
            "evidence_image": r['evidence_image'] if 'evidence_image' in r.keys() else None
        })

    # 3. Calculate statistics
    total_students = 12
    active_cameras = 0
    alerts_today = len(alerts_data)
    suspicious_students = len(set(a['student_id'] for a in alerts_data if a.get('student_id')))
    durations = [float(str(a['duration']).rstrip('sS')) for a in alerts_data if a.get('duration') is not None]
    avg_dur = round(sum(durations) / len(durations), 1) if durations else 0.0

    return jsonify({
        "success": True,
        "active_classroom": {
            "id": "CSE-301",
            "code": "CSE301",
            "name": "Computer Science Hall 301"
        },
        "statistics": {
            "total_students": total_students,
            "active_cameras": active_cameras,
            "alerts_today": alerts_today,
            "suspicious_students": suspicious_students,
            "avg_usage_duration": avg_dur
        },
        "classrooms": cls_data,
        "alerts": alerts_data
    }), 200


@teacher_bp.route('/classrooms', methods=['GET'], strict_slashes=False)
def get_teacher_classrooms():
    user = get_authenticated_user(request)
    if not user:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    user_id = user.get('user_id')
    user_role = str(user.get('role', '')).upper()

    conn = get_db_connection()
    cursor = conn.cursor()

    if user_role == 'ADMIN':
        cursor.execute("SELECT * FROM classrooms ORDER BY id")
        rows = cursor.fetchall()
        cls_list = []
        for r in rows:
            cursor.execute("SELECT COUNT(*) FROM seats WHERE classroom_id = ?", (r['id'],))
            s_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM cameras WHERE classroom_id = ? OR classroom_id = ?", (r['id'], r['code']))
            c_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM alerts WHERE classroom_id = ? OR camera_id IN (SELECT id FROM cameras WHERE classroom_id = ?)", (r['id'], r['id']))
            a_count = cursor.fetchone()[0]

            cls_list.append({
                "id": r['id'],
                "name": r['name'],
                "code": r['code'],
                "students_count": s_count or 12,
                "cameras_count": c_count or 2,
                "total_alerts": a_count,
                "is_active": True,
                "status": "ACTIVE"
            })
        conn.close()
        return jsonify({"success": True, "classrooms": cls_list})

    # Fetch authorized classrooms for Teacher (Section 12, 26, 28)
    auth_cls_ids = get_teacher_authorized_classrooms(user_id)
    active_sess = TEACHER_SESSIONS.get(user_id)
    active_cls_id = active_sess.get('classroom_id') if (active_sess and active_sess.get('monitoring_active')) else None

    cls_list = []
    for cid in auth_cls_ids:
        cursor.execute("SELECT * FROM classrooms WHERE id = ? OR code = ?", (cid, cid))
        r = cursor.fetchone()
        if not r:
            continue

        c_id = r['id']
        c_code = r['code']
        c_name = r['name']

        cursor.execute("SELECT COUNT(*) FROM seats WHERE classroom_id = ? OR classroom_id = ?", (c_id, c_code))
        s_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM cameras WHERE classroom_id = ? OR classroom_id = ?", (c_id, c_code))
        c_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM alerts WHERE classroom_id = ? OR classroom_id = ? OR camera_id IN (SELECT id FROM cameras WHERE classroom_id = ?)", (c_id, c_code, c_id))
        a_count = cursor.fetchone()[0]

        is_active = (c_id == active_cls_id or c_code == active_cls_id)

        cls_list.append({
            "id": c_id,
            "name": c_name,
            "code": c_code,
            "students_count": s_count or 12,
            "cameras_count": c_count or 2,
            "total_alerts": a_count,
            "is_active": is_active,
            "status": "ACTIVE" if is_active else "HISTORICAL"
        })

    conn.close()
    return jsonify({
        "success": True,
        "classrooms": cls_list
    })

@teacher_bp.route('/cameras', methods=['GET'], strict_slashes=False)
def get_teacher_cameras():
    user = get_authenticated_user(request)
    if not user:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    user_id = user.get('user_id')
    user_role = str(user.get('role', '')).upper()

    if user_role == 'ADMIN':
        if camera_manager:
            return jsonify({"success": True, "cameras": camera_manager.get_all_statuses()})
        return jsonify({"success": True, "cameras": []})

    sess = get_teacher_session(user_id)
    if not sess or not sess.get('monitoring_active'):
        return jsonify({"success": True, "cameras": [], "monitoring_active": False})

    allowed_cams = sess.get('cameras', [])
    filtered = camera_manager.get_all_statuses(camera_ids=allowed_cams) if camera_manager else []

    return jsonify({
        "success": True,
        "monitoring_active": True,
        "classroom_id": sess['classroom_id'],
        "cameras": filtered
    })

@teacher_bp.route('/debug/state', methods=['GET'], strict_slashes=False)
def get_teacher_debug_state():
    user = get_authenticated_user(request)
    if not user:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    user_id = user.get('user_id')
    sess = get_teacher_session(user_id)
    auth_cls = get_teacher_authorized_classrooms(user_id)

    conn = get_db_connection()
    cursor = conn.cursor()
    today_start = datetime.datetime.now().strftime("%Y-%m-%d 00:00:00")
    cursor.execute("SELECT COUNT(*) FROM alerts WHERE timestamp >= ?", (today_start,))
    alerts_today_cnt = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM alerts")
    total_alerts_cnt = cursor.fetchone()[0]
    conn.close()

    print("\n========================================")
    print("TEACHER DEBUG STATE")
    print("========================================")
    print(f"AUTHENTICATED TEACHER: {user_id} ({user.get('email')})")
    print(f"ACTIVE SESSION TEACHER: {sess.get('user_id') if sess else 'None'}")
    print(f"ACTIVE CLASSROOM: {sess.get('classroom_id') if sess else 'None'}")
    print(f"AUTHORIZED CLASSROOMS: {auth_cls}")
    print(f"CAMERAS: {sess.get('cameras') if sess else []}")
    print(f"ALERTS TODAY: {alerts_today_cnt}")
    print(f"TOTAL ALERTS: {total_alerts_cnt}")
    print("========================================\n")

    return jsonify({
        "teacher_id": user_id,
        "email": user.get('email'),
        "active_session": {
            "active": bool(sess and sess.get('monitoring_active')),
            "classroom_id": sess.get('classroom_id') if sess else None,
            "classroom_code": sess.get('classroom_code') if sess else None,
            "cameras": sess.get('cameras') if sess else []
        },
        "authorized_classrooms": auth_cls,
        "students": 12,
        "cameras": sess.get('cameras') if sess else [],
        "alerts_today": alerts_today_cnt,
        "total_alerts": total_alerts_cnt
    })

@teacher_bp.route('/alerts', methods=['GET'], strict_slashes=False)
def get_teacher_alerts():
    user = get_authenticated_user(request)
    if not user:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    user_id = user.get('user_id')
    user_role = str(user.get('role', '')).upper()
    req_cls = request.args.get('classroom_id')

    conn = get_db_connection()
    cursor = conn.cursor()

    if user_role == 'ADMIN':
        if req_cls and req_cls != 'All':
            cursor.execute("SELECT * FROM alerts WHERE classroom_id = ? OR camera_id IN (SELECT id FROM cameras WHERE classroom_id = ?) ORDER BY timestamp DESC, id DESC LIMIT 100", (req_cls, req_cls))
        else:
            cursor.execute("SELECT * FROM alerts ORDER BY timestamp DESC, id DESC LIMIT 100")
        rows = cursor.fetchall()
    else:
        auth_cls_ids = get_teacher_authorized_classrooms(user_id)
        if not auth_cls_ids:
            conn.close()
            return jsonify({"success": True, "alerts": [], "total": 0})

        target_cls_list = auth_cls_ids
        if req_cls and req_cls != 'All' and req_cls != 'All My Classrooms':
            # Verify teacher is authorized to view this historical classroom (Section 13)
            matching = [c for c in auth_cls_ids if c.upper() == req_cls.upper() or c.replace('-', '').upper() == req_cls.replace('-', '').upper()]
            if not matching:
                conn.close()
                return jsonify({"success": True, "alerts": [], "total": 0})
            target_cls_list = matching

        placeholders = ', '.join(['?'] * len(target_cls_list))
        query = f"""
            SELECT * FROM alerts 
            WHERE (classroom_id IN ({placeholders}) OR seat_id IN (SELECT id FROM seats WHERE classroom_id IN ({placeholders})))
            ORDER BY timestamp DESC, id DESC LIMIT 100
        """
        params = list(target_cls_list) + list(target_cls_list)
        cursor.execute(query, params)
        rows = cursor.fetchall()

    conn.close()

    alerts = []
    for r in rows:
        alerts.append({
            "id": r['id'],
            "classroom_id": r['classroom_id'] if 'classroom_id' in r.keys() else 'CSE-301',
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

    return jsonify({
        "success": True,
        "alerts": alerts,
        "total": len(alerts)
    })

@teacher_bp.route('/notifications/stream', methods=['GET'], strict_slashes=False)
def teacher_notifications_stream():
    user = get_authenticated_user(request)
    if not user:
        return jsonify({"success": False, "message": "Unauthorized: Authentication required"}), 401

    role = str(user.get('role', '')).upper()
    if role != 'TEACHER':
        return jsonify({"success": False, "message": "Access denied: Classroom notifications are restricted to teachers only"}), 403

    teacher_id = user.get('user_id')

    def generate():
        q = sse_manager.add_client(teacher_id)
        yield f"data: {json.dumps({'type': 'CONNECTED', 'teacher_id': teacher_id})}\n\n"
        try:
            while True:
                try:
                    msg = q.get(timeout=15)
                    yield msg
                except queue.Empty:
                    yield ": keepalive\n\n"
        finally:
            sse_manager.remove_client(teacher_id, q)

    return Response(generate(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'X-Accel-Buffering': 'no'
    })

@teacher_bp.route('/push/vapid-public-key', methods=['GET'], strict_slashes=False)
def get_vapid_public_key():
    user = get_authenticated_user(request)
    if not user:
        return jsonify({"success": False, "message": "Unauthorized: Authentication required"}), 401

    role = str(user.get('role', '')).upper()
    if role != 'TEACHER':
        return jsonify({"success": False, "message": "Access denied: Push notifications are restricted to teachers only"}), 403

    return jsonify({
        "success": True,
        "publicKey": push_service.get_public_key()
    }), 200

@teacher_bp.route('/push/subscribe', methods=['POST'], strict_slashes=False)
def subscribe_push_notification():
    user = get_authenticated_user(request)
    if not user:
        return jsonify({"success": False, "message": "Unauthorized: Authentication required"}), 401

    role = str(user.get('role', '')).upper()
    if role != 'TEACHER':
        return jsonify({"success": False, "message": "Access denied: Push notifications are restricted to teachers only"}), 403

    teacher_id = user.get('user_id')
    data = request.get_json(silent=True) or {}
    success, err = push_service.save_subscription(teacher_id, data)

    if not success:
        return jsonify({"success": False, "message": f"Subscription failed: {err}"}), 400

    return jsonify({"success": True, "message": "Push subscription saved successfully"}), 200

@teacher_bp.route('/monitoring/health', methods=['GET'], strict_slashes=False)
def get_monitoring_health():
    user = get_authenticated_user(request)
    if not user:
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    user_id = user.get('user_id')
    sess = TEACHER_SESSIONS.get(user_id)
    monitoring_active = bool(sess and sess.get('monitoring_active'))

    workers_info = []
    if sess and camera_manager:
        for cid in sess.get('cameras', []):
            w = camera_manager.get_worker(cid)
            if w:
                st = w.get_status()
                workers_info.append({
                    "camera": cid,
                    "status": "RUNNING" if w.running else "STOPPED",
                    "ai_detection": True,
                    "total_frames": w.successful_frames_read,
                    "fps": w.fps,
                    "last_frame_time": datetime.datetime.fromtimestamp(w.last_successful_frame_time).isoformat() if w.last_successful_frame_time else None
                })

    return jsonify({
        "success": True,
        "monitoring_active": monitoring_active,
        "classroom": sess.get('classroom_code') if sess else None,
        "workers": workers_info
    }), 200



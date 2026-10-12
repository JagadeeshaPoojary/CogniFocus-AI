from flask import Blueprint, Response, request, jsonify
import cv2
import time
from database.db import get_db_connection

cameras_bp = Blueprint('cameras', __name__)

camera_manager = None

def init_camera_routes(cm_instance):
    global camera_manager
    camera_manager = cm_instance

@cameras_bp.route('', methods=['GET'])
def get_cameras():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM cameras ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    
    cameras = []
    for r in rows:
        cameras.append({
            "id": r['id'],
            "name": r['name'],
            "classroom_id": r['classroom_id'],
            "source": r['source'],
            "status": r['status'],
            "fps": r['fps'],
            "last_active": r['last_active']
        })
    return jsonify({"success": True, "data": cameras})

@cameras_bp.route('/status', methods=['GET'])
def camera_status():
    if not camera_manager:
        return jsonify({"success": False, "message": "Camera Manager not initialized"}), 500
        
    camera_list = camera_manager.get_all_statuses()
    return jsonify({
        "success": True,
        "cameras": camera_list
    })

@cameras_bp.route('/<cam_id>/debug', methods=['GET'])
def camera_debug(cam_id):
    if not camera_manager:
        return jsonify({"success": False, "message": "Camera Manager not initialized"}), 500
        
    debug_info = camera_manager.get_camera_debug(cam_id)
    return jsonify(debug_info)

def check_teacher_camera_access(cam_id):
    try:
        from routes.teacher import get_authenticated_user, get_teacher_session
        user = get_authenticated_user(request)
        if user and str(user.get('role', '')).upper() == 'TEACHER':
            user_id = user.get('user_id')
            sess = get_teacher_session(user_id)
            if not sess or not sess.get('monitoring_active'):
                return False, ("Classroom access required before viewing camera stream.", 403)
            allowed_cams = sess.get('cameras', [])
            if cam_id not in allowed_cams:
                return False, (f"Forbidden: Camera {cam_id} is outside your active classroom.", 403)
    except Exception as err:
        print(f"[Camera Access Security Error] {err}")
    return True, None

@cameras_bp.route('/<cam_id>/frame.jpg', methods=['GET'])
def camera_frame_jpg(cam_id):
    if not camera_manager:
        return jsonify({"success": False, "message": "Camera Manager not initialized"}), 500

    allowed, err_resp = check_teacher_camera_access(cam_id)
    if not allowed:
        return jsonify({"success": False, "message": err_resp[0]}), err_resp[1]

    frame = camera_manager.get_latest_frame(cam_id)
    if frame is None or frame.size == 0:
        import numpy as np
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(blank, f"NO FRAME AVAILABLE ({cam_id})", (140, 240),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        success, buffer = cv2.imencode(".jpg", blank)
    else:
        success, buffer = cv2.imencode(".jpg", frame)

    if not success:
        return jsonify({"success": False, "message": "Failed to encode frame"}), 500

    return Response(buffer.tobytes(), mimetype='image/jpeg')

@cameras_bp.route('/<cam_id>/stream', methods=['GET'])
def camera_stream(cam_id):
    if not camera_manager:
        return jsonify({"success": False, "message": "Camera Manager not initialized"}), 500

    allowed, err_resp = check_teacher_camera_access(cam_id)
    if not allowed:
        return jsonify({"success": False, "message": err_resp[0]}), err_resp[1]

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


@cameras_bp.route('', methods=['POST'])
def create_camera():
    data = request.get_json() or {}
    cam_id = data.get('id', '').strip().upper()
    name = data.get('name', '').strip()
    classroom_id = data.get('classroom_id', 'CSE-301')
    source = data.get('source', '0').strip()
    
    if not cam_id or not name:
        return jsonify({"success": False, "message": "Camera ID and Name are required"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM cameras WHERE id = ?", (cam_id,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"success": False, "message": "Camera ID already exists"}), 400
        
    cursor.execute('''
        INSERT INTO cameras (id, name, classroom_id, source, status, fps)
        VALUES (?, ?, ?, ?, 'Online', 28)
    ''', (cam_id, name, classroom_id, source))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": f"Camera {cam_id} created successfully"}), 201

@cameras_bp.route('/<cam_id>', methods=['PUT'])
def update_camera(cam_id):
    data = request.get_json() or {}
    name = data.get('name')
    classroom_id = data.get('classroom_id')
    source = data.get('source')
    status = data.get('status')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM cameras WHERE id = ?", (cam_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"success": False, "message": "Camera not found"}), 404
        
    cursor.execute('''
        UPDATE classrooms
        SET name = COALESCE(?, name),
            classroom_id = COALESCE(?, classroom_id),
            source = COALESCE(?, source),
            status = COALESCE(?, status)
        WHERE id = ?
    ''', (name, classroom_id, source, status, cam_id))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": f"Camera {cam_id} updated successfully"})

@cameras_bp.route('/<cam_id>', methods=['DELETE'])
def delete_camera(cam_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cameras WHERE id = ?", (cam_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": f"Camera {cam_id} removed successfully"})

@cameras_bp.route('/<cam_id>/test', methods=['POST'])
def test_camera(cam_id):
    if camera_manager:
        worker = camera_manager.get_worker(cam_id)
        if worker and worker.opened and worker.frame_available:
            return jsonify({"success": True, "status": "Online", "message": "Camera connection active and reading physical frames!"})
            
    return jsonify({"success": False, "status": "Offline", "message": "Camera device not actively capturing frames."})

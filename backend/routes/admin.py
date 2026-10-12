from flask import Blueprint, jsonify
from database.db import get_db_connection

admin_bp = Blueprint('admin', __name__)

camera_manager = None

def init_admin_routes(cm_instance):
    global camera_manager
    camera_manager = cm_instance

@admin_bp.route('/start-monitoring', methods=['POST'])
def start_monitoring():
    if not camera_manager:
        return jsonify({"success": False, "message": "Camera Manager not initialized"}), 500
        
    active_cameras = camera_manager.start_all()
    
    return jsonify({
        "success": True,
        "message": f"Successfully initialized {len(active_cameras)} camera monitoring workers",
        "monitoring": True,
        "cameras": active_cameras
    })

@admin_bp.route('/stop-monitoring', methods=['POST'])
def stop_monitoring():
    if not camera_manager:
        return jsonify({"success": False, "message": "Camera Manager not initialized"}), 500
        
    camera_manager.stop_all()
    return jsonify({
        "success": True,
        "message": "All camera workers stopped and hardware devices released successfully",
        "monitoring": False
    })

@admin_bp.route('/cameras/discover', methods=['GET'])
def discover_cameras():
    if not camera_manager:
        return jsonify({"success": False, "message": "Camera Manager not initialized"}), 500
        
    cameras = camera_manager.discover_cameras()
    return jsonify({"success": True, "cameras": cameras})

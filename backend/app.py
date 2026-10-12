import os
import sys
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.seed import seed_db
from ai.camera_manager import CameraManager
from routes.auth import auth_bp
from routes.admin import admin_bp, init_admin_routes
from routes.monitor import monitor_bp, init_monitor_routes
from routes.alerts import alerts_bp
from routes.classrooms import classrooms_bp
from routes.cameras import cameras_bp, init_camera_routes
from routes.students import students_bp
from routes.reports import reports_bp
from routes.config_route import config_bp, load_file_config
from routes.teacher import teacher_bp, init_teacher_routes
from routes.notifications import notifications_bp

def create_app():
    seed_db()
    
    app = Flask(__name__)
    CORS(app, resources={r"/*": {"origins": "*"}}, allow_headers=["Content-Type", "Authorization", "X-Requested-With"], methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    
    cfg = load_file_config()
    
    # Instantiate Multi-Camera Manager (cameras start on-demand for Admin / Teacher session)
    camera_manager = CameraManager(config=cfg)
    from services.monitoring_manager import monitoring_manager
    monitoring_manager.init_camera_manager(camera_manager)
    
    # Initialize Routes
    init_admin_routes(camera_manager)
    init_monitor_routes(camera_manager)
    init_camera_routes(camera_manager)
    init_teacher_routes(camera_manager)

    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(monitor_bp, url_prefix='/api/monitor')
    app.register_blueprint(teacher_bp, url_prefix='/api/teacher')
    app.register_blueprint(alerts_bp, url_prefix='/api/alerts')
    app.register_blueprint(classrooms_bp, url_prefix='/api/classrooms')
    app.register_blueprint(cameras_bp, url_prefix='/api/cameras')
    app.register_blueprint(students_bp, url_prefix='/api/students')
    app.register_blueprint(reports_bp, url_prefix='/api/reports')
    app.register_blueprint(config_bp, url_prefix='/api/config')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')

    
    # Serve Student Evidence Images
    EVIDENCE_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'evidence')
    os.makedirs(EVIDENCE_FOLDER, exist_ok=True)
    
    @app.route('/evidence/<path:filename>')
    def serve_evidence(filename):
        safe_rel = os.path.normpath(filename).replace('\\', '/')
        if safe_rel.startswith('..') or '..' in safe_rel.split('/'):
            return jsonify({"success": False, "message": "Invalid evidence file path"}), 400

        full_path = os.path.normpath(os.path.join(EVIDENCE_FOLDER, safe_rel))
        if not os.path.exists(full_path) or not os.path.isfile(full_path):
            return jsonify({"success": False, "message": "Evidence image file not found on disk"}), 404

        dir_name = os.path.dirname(full_path)
        file_name = os.path.basename(full_path)
        return send_from_directory(dir_name, file_name)
    
    @app.route('/')
    def root():
        return jsonify({
            "status": "online",
            "app": "CogniFocus-AI Backend",
            "version": "2.0.0",
            "active_cameras": len(camera_manager.workers) if camera_manager else 0
        })
        
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "message": "API endpoint not found"}), 404

    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500

    return app

if __name__ == '__main__':
    app = create_app()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cert_path = os.path.normpath(os.path.join(base_dir, '..', 'frontend', 'certs', 'cert.pem'))
    key_path = os.path.normpath(os.path.join(base_dir, '..', 'frontend', 'certs', 'dev.key'))
    
    ssl_ctx = None
    if os.path.exists(cert_path) and os.path.exists(key_path):
        ssl_ctx = (cert_path, key_path)
        print(f"[CogniFocus-AI] HTTPS SSL Enabled: {cert_path}")
        print("[CogniFocus-AI] Starting Flask Multi-Camera server on https://0.0.0.0:5000 ...")
    else:
        print("[CogniFocus-AI] Starting Flask Multi-Camera server on http://0.0.0.0:5000 ...")
        
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True, ssl_context=ssl_ctx)


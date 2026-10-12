from flask import Blueprint, request, jsonify
import json
import os
from database.db import get_db_connection

config_bp = Blueprint('config', __name__)
CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'config.json')

def load_file_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "camera_id": 0,
        "camera_source": "0",
        "confidence": 0.5,
        "alert_time": 10,
        "alert_cooldown": 30,
        "dashboard_width": 400,
        "beep_frequency": 1000,
        "beep_duration": 500,
        "model_type": "yolov8n-pose.pt",
        "simulation_mode": False
    }

def save_file_config(cfg):
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print(f"[Config Save Error] {e}")

@config_bp.route('', methods=['GET'])
def get_configuration():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM configurations")
    rows = cursor.fetchall()
    conn.close()
    
    file_cfg = load_file_config()
    db_cfg = {r['key']: r['value'] for r in rows}
    
    merged = {
        "camera_id": db_cfg.get("camera_id", file_cfg.get("camera_id", "0")),
        "camera_source": db_cfg.get("camera_source", file_cfg.get("camera_source", "0")),
        "confidence": float(db_cfg.get("confidence", file_cfg.get("confidence", 0.5))),
        "alert_time": int(db_cfg.get("alert_time", file_cfg.get("alert_time", 10))),
        "alert_cooldown": int(db_cfg.get("alert_cooldown", file_cfg.get("alert_cooldown", 30))),
        "dashboard_width": int(db_cfg.get("dashboard_width", file_cfg.get("dashboard_width", 400))),
        "beep_frequency": int(db_cfg.get("beep_frequency", file_cfg.get("beep_frequency", 1000))),
        "beep_duration": int(db_cfg.get("beep_duration", file_cfg.get("beep_duration", 500))),
        "model_type": db_cfg.get("model_type", file_cfg.get("model_type", "yolov8n-pose.pt")),
        "simulation_mode": db_cfg.get("simulation_mode", "false").lower() == "true" or file_cfg.get("simulation_mode", False)
    }
    
    return jsonify({"success": True, "data": merged})

@config_bp.route('', methods=['PUT'])
def update_configuration():
    data = request.get_json() or {}
    
    file_cfg = load_file_config()
    file_cfg.update(data)
    save_file_config(file_cfg)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    for k, v in data.items():
        cursor.execute("INSERT OR REPLACE INTO configurations (key, value) VALUES (?, ?)", (k, str(v)))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": "System configuration updated successfully", "data": file_cfg})

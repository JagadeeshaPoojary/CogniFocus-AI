import os
import sys
import datetime
import threading

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class MonitoringManager:
    def __init__(self):
        self.camera_manager = None
        self.lock = threading.Lock()

    def init_camera_manager(self, cm_instance):
        self.camera_manager = cm_instance

    def start_classroom_monitoring(self, teacher_id, classroom_id, classroom_code, camera_specs):
        """
        Starts independent backend AI camera workers for specified classroom cameras.
        Does NOT rely on browser connections or frontend stream consumers.
        """
        if not self.camera_manager:
            print("[MonitoringManager] Warning: CameraManager not bound yet.")
            return False

        with self.lock:
            print("\n====================================")
            print("MONITORING STARTED")
            print(f"Teacher ID: {teacher_id}")
            print(f"Classroom: {classroom_id} ({classroom_code})")
            
            cam_ids = [c["camera_id"] for c in camera_specs]
            for cid in cam_ids:
                print(f"{cid} WORKER: RUNNING")
            print("AI ENGINE: RUNNING")
            print("====================================\n")

            # Start camera workers via CameraManager
            active_info = self.camera_manager.start_all(camera_specs)
            return active_info

    def stop_classroom_monitoring(self, teacher_id, camera_ids):
        if not self.camera_manager:
            return False

        with self.lock:
            print("\n====================================")
            print("MONITORING STOPPING")
            print(f"Teacher ID: {teacher_id}")
            for cid in camera_ids:
                print(f"{cid} WORKER: STOPPING")
            print("====================================\n")

            self.camera_manager.stop_cameras(camera_ids)
            return True

monitoring_manager = MonitoringManager()

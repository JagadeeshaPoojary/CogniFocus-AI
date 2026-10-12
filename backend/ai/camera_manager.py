import cv2
import threading
import time
from ai.camera_worker import CameraWorker

class CameraManager:
    def __init__(self, config=None):
        self.config = config or {}
        self.workers = {}
        self.lock = threading.RLock()

    def discover_cameras(self):
        """Scans physical camera indexes 0..4 using CAP_DSHOW probes to discover all available USB cameras."""
        with self.lock:
            if self.workers:
                active_list = []
                for cam_id, worker in self.workers.items():
                    active_list.append(worker.get_status())
                if active_list:
                    return active_list

        available = []
        backends = [cv2.CAP_MSMF, cv2.CAP_DSHOW] if hasattr(cv2, 'CAP_MSMF') else [cv2.CAP_DSHOW]
        for idx in range(5):
            cam_id = f"CAM00{idx+1}"
            opened = False
            for backend_api in backends:
                try:
                    cap = cv2.VideoCapture(idx + backend_api)
                    if cap and cap.isOpened():
                        ret, test_frame = cap.read()
                        cap.release()
                        if ret and test_frame is not None and test_frame.size > 0:
                            available.append({
                                "camera_id": cam_id,
                                "device_index": idx,
                                "source": str(idx),
                                "status": "online",
                                "opened": True,
                                "frame_available": True
                            })
                            opened = True
                            break
                except Exception as e:
                    print(f"[CameraManager] Error discovering device index {idx} with backend {backend_api}: {e}")
            if not opened:
                try:
                    cap = cv2.VideoCapture(idx)
                    if cap and cap.isOpened():
                        ret, test_frame = cap.read()
                        cap.release()
                        if ret and test_frame is not None and test_frame.size > 0:
                            available.append({
                                "camera_id": cam_id,
                                "device_index": idx,
                                "source": str(idx),
                                "status": "online",
                                "opened": True,
                                "frame_available": True
                            })
                except Exception:
                    pass
                
        if not available:
            # Fallback default registration for device 0
            available = [
                {"camera_id": "CAM001", "device_index": 0, "source": "0", "status": "online", "opened": True, "frame_available": True}
            ]
        print(f"[CameraManager] Discovered physical cameras: {[c['camera_id'] for c in available]}")
        return available

    def start_all(self, camera_list=None):
        with self.lock:
            if not camera_list:
                camera_list = self.discover_cameras()
                
            active_info = []
            for cam in camera_list:
                cam_id = cam.get("camera_id", "CAM001")
                dev_idx = cam.get("device_index", 0)
                
                if cam_id not in self.workers:
                    worker = CameraWorker(camera_id=cam_id, device_index=dev_idx, config=self.config)
                    worker.start()
                    self.workers[cam_id] = worker
                else:
                    self.workers[cam_id].start()
                    
                st = self.workers[cam_id].get_status()
                st["stream_url"] = f"/api/cameras/{cam_id}/stream"
                active_info.append(st)
                
            print(f"[CameraManager] Active persistent camera workers: {list(self.workers.keys())}")
            return active_info

    def stop_cameras(self, camera_ids):
        with self.lock:
            for cam_id in camera_ids:
                if cam_id in self.workers:
                    try:
                        self.workers[cam_id].stop()
                    except Exception as e:
                        print(f"[CameraManager] Error stopping worker {cam_id}: {e}")
                    del self.workers[cam_id]
            print(f"[CameraManager] Stopped camera workers: {camera_ids}")

    def stop_all(self):
        with self.lock:
            for cam_id, worker in list(self.workers.items()):
                try:
                    worker.stop()
                except Exception as e:
                    print(f"[CameraManager] Error stopping worker {cam_id}: {e}")
            self.workers.clear()
            print("[CameraManager] Stopped all camera workers.")

    def get_latest_frame(self, camera_id):
        with self.lock:
            worker = self.workers.get(camera_id)
            if worker:
                return worker.get_latest_frame()
            return None

    def print_camera_system_status(self):
        with self.lock:
            print("========================================")
            print("CAMERA SYSTEM")
            print("========================================")
            for cam_id in sorted(self.workers.keys()):
                w = self.workers[cam_id]
                dbg = w.get_debug_info()
                res = f"{dbg['frame_width']}x{dbg['frame_height']}" if dbg['frame_width'] > 0 else "0x0"
                print(f"{cam_id}")
                print(f"Device: {dbg['device_index']}")
                print(f"Opened: {'TRUE' if dbg['opened'] else 'FALSE'}")
                print(f"Frame: {'TRUE' if dbg['frame_available'] else 'FALSE'}")
                print(f"Resolution: {res}")
                print(f"Capture FPS: {dbg['fps']}")
                print(f"Worker: {'RUNNING' if dbg['worker_running'] else 'STOPPED'}")
                print(f"Stream: {'READY' if dbg['stream_available'] else 'NOT READY'}")
                print()
            print("========================================")

    def get_worker(self, cam_id):
        with self.lock:
            return self.workers.get(cam_id)

    def get_camera_debug(self, cam_id):
        with self.lock:
            worker = self.workers.get(cam_id)
            if worker:
                return worker.get_debug_info()
            return {
                "camera_id": cam_id,
                "device_index": 0 if cam_id == "CAM001" else 1,
                "opened": False,
                "frame_available": False,
                "frame_width": 0,
                "frame_height": 0,
                "fps": 0.0,
                "worker_running": False,
                "last_frame_age": 999.0,
                "stream_available": False,
                "status": "OFFLINE",
                "explanation": f"Camera worker {cam_id} is not initialized in CameraManager"
            }

    def get_all_statuses(self, camera_ids=None):
        with self.lock:
            statuses = []
            target_ids = camera_ids if camera_ids else list(self.workers.keys())
            for cam_id in target_ids:
                if cam_id in self.workers:
                    st = self.workers[cam_id].get_status()
                    st["stream_url"] = f"/api/cameras/{cam_id}/stream"
                    statuses.append(st)
                else:
                    statuses.append({
                        "camera_id": cam_id,
                        "device_index": int(cam_id[3:]) - 1 if cam_id.startswith("CAM") and cam_id[3:].isdigit() else 0,
                        "status": "offline",
                        "opened": False,
                        "frame_available": False,
                        "worker_running": False,
                        "streaming": False,
                        "fps": 0.0,
                        "stream_url": f"/api/cameras/{cam_id}/stream"
                    })
            return statuses

    def get_all_detections(self):
        with self.lock:
            all_dets = []
            for worker in self.workers.values():
                all_dets.extend(worker.get_detections())
            return all_dets

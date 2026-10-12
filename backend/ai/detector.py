import cv2
import numpy as np
import time
import math
import threading
import os
import sqlite3
import datetime
from ultralytics import YOLO
from database.db import get_db_connection

class ClassroomMonitor:
    def __init__(self, camera_id="CAM001", device_index=0, camera_source="0", config=None):
        self.camera_id = camera_id
        self.device_index = int(device_index) if str(device_index).isdigit() else 0
        self.camera_source = str(camera_source)
        self.config = config or {}
        
        self.confidence_threshold = float(self.config.get("confidence", 0.5))
        self.alert_time = int(self.config.get("alert_time", 5))
        self.alert_cooldown = int(self.config.get("alert_cooldown", 30))
        
        self.root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.models_dir = os.path.join(self.root_dir, "models")
        self.evidence_dir = os.path.join(self.root_dir, "backend", "evidence", self.camera_id)
        os.makedirs(self.evidence_dir, exist_ok=True)
        
        # Load YOLO models
        self.pose_model_path = os.path.join(self.models_dir, "yolov8n-pose.pt")
        self.object_model_path = os.path.join(self.models_dir, "yolov8n.pt")
        
        self.pose_model = None
        self.object_model = None
        self._load_models()
        
        # Threading & Hardware State
        self.running = False
        self.thread = None
        self.cap = None
        
        self.opened = False
        self.frame_available = False
        self.streaming = False
        self.status = "offline"
        self.frame_size = "0x0"
        
        self.current_frame = None
        self.latest_frame_bytes = None
        self.lock = threading.Lock()
        
        # Telemetry state
        self.active_students_count = 0
        self.suspicious_students_count = 0
        self.fps = 0.0
        self.last_update_timestamp = ""
        self.current_detections = []
        
        # Duration & Cooldown Tracking per seat
        self.seat_durations = {}    # seat_id -> start_time
        self.last_alert_times = {}  # seat_id -> timestamp

    def _load_models(self):
        try:
            if os.path.exists(self.pose_model_path):
                self.pose_model = YOLO(self.pose_model_path)
            else:
                self.pose_model = YOLO("yolov8n-pose.pt")
                
            if os.path.exists(self.object_model_path):
                self.object_model = YOLO(self.object_model_path)
            else:
                self.object_model = YOLO("yolov8n.pt")
        except Exception as e:
            print(f"[{self.camera_id}] Error loading YOLO models: {e}")

    def start(self):
        if self.running:
            return True
            
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        print(f"[{self.camera_id}] Background camera worker thread launched (Index: {self.device_index})")
        return True

    def stop(self):
        self.running = False
        self.opened = False
        self.frame_available = False
        self.streaming = False
        self.status = "offline"
        
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        print(f"[{self.camera_id}] Camera worker stopped and hardware device released.")

    def _run_loop(self):
        # Open Physical Camera using DirectShow on Windows
        try:
            self.cap = cv2.VideoCapture(self.device_index, cv2.CAP_DSHOW)
            if not self.cap.isOpened():
                # Fallback to default backend if DSHOW fails
                self.cap = cv2.VideoCapture(self.device_index)
        except Exception as e:
            print(f"[{self.camera_id}] OpenCV capture error: {e}")

        if self.cap and self.cap.isOpened():
            self.opened = True
            self.status = "online"
            print(f"[{self.camera_id}] Physical camera device opened successfully!")
        else:
            self.opened = False
            self.status = "camera_error"
            print(f"[{self.camera_id}] Failed to open physical camera device index {self.device_index}")

        prev_time = time.time()
        log_counter = 0

        while self.running:
            start_t = time.time()
            
            if not self.opened or self.cap is None or not self.cap.isOpened():
                self.frame_available = False
                self.streaming = False
                self.status = "camera_error"
                frame_to_encode = self._create_error_frame("CAMERA DEVICE NOT ACCESSIBLE")
                detections = []
            else:
                ret, raw_frame = self.cap.read()
                if not ret or raw_frame is None:
                    self.frame_available = False
                    self.streaming = False
                    self.status = "frame_error"
                    frame_to_encode = self._create_error_frame("FRAME READ ERROR - RECONNECTING...")
                    detections = []
                else:
                    self.opened = True
                    self.frame_available = True
                    self.streaming = True
                    self.status = "online"
                    
                    fh, fw, _ = raw_frame.shape
                    self.frame_size = f"{fw}x{fh}"
                    
                    # Analyze frame with real AI pipeline
                    annotated_frame, detections = self._analyze_frame(raw_frame)
                    frame_to_encode = annotated_frame

            # Calculate FPS
            curr_time = time.time()
            self.fps = round(1.0 / max(0.001, curr_time - prev_time), 1)
            prev_time = curr_time
            
            # Encode physical frame to JPEG bytes
            _, jpeg_buffer = cv2.imencode('.jpg', frame_to_encode)
            encoded_bytes = jpeg_buffer.tobytes()

            with self.lock:
                self.current_frame = frame_to_encode
                self.latest_frame_bytes = encoded_bytes
                self.current_detections = detections
                self.active_students_count = len(detections)
                self.suspicious_students_count = sum(1 for d in detections if d.get("status") == "possible_mobile_usage")
                self.last_update_timestamp = time.strftime("%H:%M:%S")

            # Structured Debug Logging every 100 frames (~4 sec)
            log_counter += 1
            if log_counter % 100 == 0:
                print(f"{self.camera_id}: Camera opened: {self.opened} | Frame received: {self.frame_available} | Frame size: {self.frame_size} | FPS: {self.fps} | Streaming: {self.streaming}")

            elapsed = time.time() - start_t
            sleep_time = max(0.005, 0.04 - elapsed)
            time.sleep(sleep_time)

    def _analyze_frame(self, frame):
        h, w, _ = frame.shape
        detections = []
        
        if self.pose_model is None:
            return frame, detections
            
        # Run YOLO pose inference on physical camera frame
        results = self.pose_model(frame, verbose=False, conf=self.confidence_threshold)
        
        # Run phone detection if object model loaded
        phone_boxes = []
        if self.object_model:
            obj_res = self.object_model(frame, verbose=False, conf=0.35, classes=[67])
            for r in obj_res:
                if r.boxes:
                    for box in r.boxes:
                        xyxy = box.xyxy[0].cpu().numpy()
                        phone_boxes.append(xyxy)
                        cv2.rectangle(frame, (int(xyxy[0]), int(xyxy[1])), (int(xyxy[2]), int(xyxy[3])), (255, 200, 0), 2)
                        cv2.putText(frame, "Cell Phone", (int(xyxy[0]), max(15, int(xyxy[1]) - 5)),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 200, 0), 1, cv2.LINE_AA)

        for r in results:
            if not r.boxes or not r.keypoints:
                continue
                
            boxes = r.boxes.xyxy.cpu().numpy()
            keypoints = r.keypoints.data.cpu().numpy()
            
            for idx, box in enumerate(boxes):
                x1, y1, x2, y2 = map(int, box[:4])
                kpts = keypoints[idx]
                
                is_suspicious, pose_score, reason = self._eval_pose_heuristics(kpts, box, phone_boxes)
                
                cx = (x1 + x2) / 2.0
                cy = (y1 + y2) / 2.0
                seat_id = self._map_centroid_to_seat(cx, cy, w, h, idx)
                student_id = f"STU-00{idx+1}" if (idx+1) < 10 else f"STU-0{idx+1}"
                
                now_t = time.time()
                if is_suspicious:
                    if seat_id not in self.seat_durations:
                        self.seat_durations[seat_id] = now_t
                    duration = int(now_t - self.seat_durations[seat_id])
                else:
                    self.seat_durations.pop(seat_id, None)
                    duration = 0
                    
                if is_suspicious and duration >= 3:
                    box_color = (0, 0, 255) # Red
                    status_str = f"MOBILE USAGE ({duration}s)" if duration >= self.alert_time else f"POSSIBLE MOBILE USAGE ({duration}s)"
                    status_enum = "possible_mobile_usage"
                    
                    # Confirmed Alert Trigger + Student Evidence Capture
                    if duration >= self.alert_time:
                        self._trigger_alert_with_evidence(frame, [x1, y1, x2, y2], student_id, seat_id, reason, pose_score, duration)
                elif is_suspicious:
                    box_color = (0, 200, 255) # Amber
                    status_str = f"MONITORING ({duration}s)"
                    status_enum = "monitoring"
                else:
                    box_color = (0, 255, 0) # Green
                    status_str = "NORMAL"
                    status_enum = "normal"
                    
                # Draw Box & Pose Skeleton directly on real camera image
                cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)
                
                # Label box header
                label_text = f"ID: {idx+1} | {seat_id} ({student_id}) | {status_str}"
                cv2.rectangle(frame, (x1, max(0, y1 - 25)), (x1 + len(label_text)*9, max(25, y1)), (15, 20, 30), -1)
                cv2.putText(frame, label_text, (x1 + 4, max(18, y1 - 7)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, box_color, 1, cv2.LINE_AA)
                            
                self._draw_skeleton(frame, kpts, box_color)
                
                detections.append({
                    "student_id": student_id,
                    "seat": seat_id,
                    "status": status_enum,
                    "duration": duration,
                    "confidence": round(float(pose_score), 2),
                    "camera_id": self.camera_id,
                    "bbox": [x1, y1, x2, y2],
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
                })

        return frame, detections

    def _eval_pose_heuristics(self, kpts, box, phone_boxes):
        nose = kpts[0]
        l_shoulder = kpts[5]
        r_shoulder = kpts[6]
        l_wrist = kpts[9]
        r_wrist = kpts[10]
        
        is_suspicious = False
        score = 0.2
        reason = "Possible Mobile Usage"
        
        x1, y1, x2, y2 = box[:4]
        for pbox in phone_boxes:
            px1, py1, px2, py2 = pbox
            if (px1 < x2 and px2 > x1 and py1 < y2 and py2 > y1):
                is_suspicious = True
                score = 0.92
                reason = "Cell Phone Detected Near Body"
                return is_suspicious, score, reason

        if l_shoulder[2] > 0.3 and r_shoulder[2] > 0.3:
            shoulder_width = max(1.0, math.hypot(l_shoulder[0] - r_shoulder[0], l_shoulder[1] - r_shoulder[1]))
            d_l_wrist = math.hypot(l_wrist[0] - nose[0], l_wrist[1] - nose[1]) if l_wrist[2] > 0.3 else 999
            d_r_wrist = math.hypot(r_wrist[0] - nose[0], r_wrist[1] - nose[1]) if r_wrist[2] > 0.3 else 999
            min_wrist_dist = min(d_l_wrist, d_r_wrist)
            
            ratio = min_wrist_dist / shoulder_width
            neck_x = (l_shoulder[0] + r_shoulder[0]) / 2.0
            neck_y = (l_shoulder[1] + r_shoulder[1]) / 2.0
            head_tilt = math.degrees(math.atan2(abs(nose[0] - neck_x), max(1.0, neck_y - nose[1])))
            
            if ratio < 0.65 or head_tilt > 32:
                is_suspicious = True
                score = min(0.95, round(0.5 + (0.65 - ratio)*0.5 + (head_tilt/100.0), 2))
                reason = "Suspicious Posture & Hand Elevation"

        return is_suspicious, score, reason

    def _map_centroid_to_seat(self, cx, cy, img_w, img_h, index):
        cols = 3
        rows = 4
        c = min(cols - 1, int(cx / (img_w / cols)))
        r = min(rows - 1, int(cy / (img_h / rows)))
        seat_num = r * cols + c + 1
        return f"B{seat_num}"

    def _draw_skeleton(self, frame, kpts, color):
        connections = [
            (0, 1), (0, 2), (1, 3), (2, 4),
            (5, 6), (5, 7), (7, 9), (6, 8), (8, 10),
            (5, 11), (6, 12), (11, 12)
        ]
        for p1, p2 in connections:
            if kpts[p1][2] > 0.3 and kpts[p2][2] > 0.3:
                pt1 = (int(kpts[p1][0]), int(kpts[p1][1]))
                pt2 = (int(kpts[p2][0]), int(kpts[p2][1]))
                cv2.line(frame, pt1, pt2, color, 1)

    def _trigger_alert_with_evidence(self, frame, bbox, student_id, seat_id, alert_type, confidence, duration):
        now_t = time.time()
        last_t = self.last_alert_times.get(seat_id, 0)
        
        if (now_t - last_t) < self.alert_cooldown:
            return
            
        self.last_alert_times[seat_id] = now_t
        
        # Crop Student Evidence Image directly from real physical camera frame
        evidence_rel_path = self._crop_and_save_evidence(frame, bbox, student_id, seat_id)
        
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id FROM alerts WHERE seat_id = ? AND status = 'Active'
            ''', (seat_id,))
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO alerts (student_id, seat_id, camera_id, alert_type, confidence, duration, status, severity, evidence_image, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, 'Active', 'High', ?, ?)
                ''', (student_id, seat_id, self.camera_id, alert_type, confidence, duration, evidence_rel_path, datetime.datetime.now().isoformat()))
                conn.commit()
                print(f"[{self.camera_id}] REAL ALERT SAVED! Seat {seat_id}, Student {student_id}, Evidence: {evidence_rel_path}")
            conn.close()
        except Exception as e:
            print(f"[{self.camera_id}] Alert DB insertion error: {e}")

    def _crop_and_save_evidence(self, frame, bbox, student_id, seat_id):
        if frame is None or frame.size == 0:
            return None
            
        h, w, _ = frame.shape
        x1, y1, x2, y2 = bbox
        
        bw = x2 - x1
        bh = y2 - y1
        pad_w = int(bw * 0.25)
        pad_h = int(bh * 0.25)
        
        cx1 = max(0, x1 - pad_w)
        cy1 = max(0, y1 - pad_h)
        cx2 = min(w, x2 + pad_w)
        cy2 = min(h, y2 + pad_h)
        
        cropped = frame[cy1:cy2, cx1:cx2].copy()
        
        banner_h = 35
        ch, cw, _ = cropped.shape
        cv2.rectangle(cropped, (0, ch - banner_h), (cw, ch), (15, 20, 30), -1)
        cv2.rectangle(cropped, (0, ch - banner_h), (cw, ch), (0, 0, 255), 1)
        
        ts_str = time.strftime("%Y-%m-%d %H:%M:%S")
        meta_text = f"REAL EVIDENCE | {self.camera_id} | {seat_id} ({student_id}) | {ts_str}"
        cv2.putText(cropped, meta_text, (10, ch - 12),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 210, 255), 1, cv2.LINE_AA)
                    
        clean_stu = student_id.replace('-', '')
        filename = f"{self.camera_id}_{clean_stu}_{time.strftime('%Y%m%d_%H%M%S')}.jpg"
        filepath = os.path.join(self.evidence_dir, filename)
        
        cv2.imwrite(filepath, cropped)
        rel_path = f"/evidence/{self.camera_id}/{filename}"
        return rel_path

    def _create_error_frame(self, message):
        blank = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.rectangle(blank, (20, 20), (620, 460), (15, 20, 35), -1)
        cv2.rectangle(blank, (20, 20), (620, 460), (0, 0, 255), 2)
        cv2.putText(blank, f"● OFFLINE ({self.camera_id})", (180, 220),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2, cv2.LINE_AA)
        cv2.putText(blank, message, (160, 260),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1, cv2.LINE_AA)
        return blank

    def get_encoded_frame(self):
        with self.lock:
            if self.latest_frame_bytes is not None:
                return self.latest_frame_bytes
                
            blank = self._create_error_frame("INITIALIZING CAMERA...")
            _, jpeg = cv2.imencode('.jpg', blank)
            return jpeg.tobytes()

    def get_status(self):
        with self.lock:
            return {
                "camera_id": self.camera_id,
                "device_index": self.device_index,
                "status": self.status,
                "opened": self.opened,
                "frame_available": self.frame_available,
                "worker_running": self.running,
                "streaming": self.streaming,
                "fps": self.fps,
                "frame_size": self.frame_size,
                "active_students": self.active_students_count,
                "suspicious_students": self.suspicious_students_count,
                "last_updated": self.last_update_timestamp or time.strftime("%H:%M:%S")
            }

    def get_detections(self):
        with self.lock:
            return list(self.current_detections)

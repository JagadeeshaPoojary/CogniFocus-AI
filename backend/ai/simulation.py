import cv2
import numpy as np
import time
import math

class ClassroomSimulator:
    def __init__(self, camera_id="CAM001", width=1280, height=720):
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.frame_count = 0
        
        # Grid setup: 4 rows x 3 columns = 12 seats (B1 .. B12)
        self.rows = 4
        self.cols = 3
        self.seats = []
        
        margin_x = 180
        margin_top = 180
        grid_w = self.width - 2 * margin_x
        grid_h = self.height - margin_top - 60
        
        cell_w = grid_w / self.cols
        cell_h = grid_h / self.rows
        
        seat_num = 1
        for r in range(self.rows):
            for c in range(self.cols):
                seat_label = f"B{seat_num}"
                student_id = f"STU-00{seat_num}" if seat_num < 10 else f"STU-0{seat_num}"
                
                center_x = int(margin_x + c * cell_w + cell_w / 2)
                center_y = int(margin_top + r * cell_h + cell_h / 2)
                
                self.seats.append({
                    "id": seat_label,
                    "label": seat_label,
                    "student_id": student_id,
                    "row": r + 1,
                    "col": c + 1,
                    "cx": center_x,
                    "cy": center_y,
                    "w": int(cell_w * 0.75),
                    "h": int(cell_h * 0.75),
                    "status": "normal",
                    "suspicious_duration": 0,
                    "pose_score": 0.15,
                    "phone_score": 0.05
                })
                seat_num += 1

    def generate_frame(self):
        self.frame_count += 1
        t = time.time()
        
        # Dark modern background
        frame = np.ones((self.height, self.width, 3), dtype=np.uint8) * 24
        
        # Draw Classroom Smart Board Header at top
        board_x1, board_y1 = 300, 30
        board_x2, board_y2 = self.width - 300, 110
        cv2.rectangle(frame, (board_x1, board_y1), (board_x2, board_y2), (40, 50, 45), -1)
        cv2.rectangle(frame, (board_x1, board_y1), (board_x2, board_y2), (80, 160, 100), 2)
        
        board_text = f"SMART BOARD - CLASSROOM CSE-301 ({self.camera_id})"
        cv2.putText(frame, board_text, (board_x1 + 40, board_y1 + 48),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (220, 240, 225), 2, cv2.LINE_AA)
        
        detections = []
        
        # Determine suspicious seat based on camera_id
        target_seat = "B5" if self.camera_id == "CAM001" else "B8"
        
        for idx, seat in enumerate(self.seats):
            if seat["id"] == target_seat:
                cycle = int(t) % 18
                if cycle > 4:
                    seat["status"] = "suspicious"
                    seat["suspicious_duration"] = min(60, cycle - 4 + int(math.sin(self.frame_count * 0.1) * 2))
                    seat["pose_score"] = 0.89
                    seat["phone_score"] = 0.85
                else:
                    seat["status"] = "normal"
                    seat["suspicious_duration"] = 0
                    seat["pose_score"] = 0.15
                    seat["phone_score"] = 0.04
            else:
                seat["status"] = "normal"
                seat["suspicious_duration"] = 0
                seat["pose_score"] = 0.10 + 0.05 * math.sin(t + idx)
                seat["phone_score"] = 0.02
                
            bx1 = seat["cx"] - seat["w"] // 2
            by1 = seat["cy"] - seat["h"] // 2
            bx2 = seat["cx"] + seat["w"] // 2
            by2 = seat["cy"] + seat["h"] // 2
            
            if seat["status"] == "suspicious":
                color = (0, 70, 240)
                bg_color = (10, 15, 60)
            else:
                color = (70, 180, 80)
                bg_color = (20, 30, 25)
                
            cv2.rectangle(frame, (bx1, by1), (bx2, by2), bg_color, -1)
            cv2.rectangle(frame, (bx1, by1), (bx2, by2), color, 2)
            
            cv2.putText(frame, f"{seat['id']} ({seat['student_id']})", (bx1 + 10, by1 + 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (230, 230, 230), 1, cv2.LINE_AA)
            
            scx = seat["cx"]
            scy = seat["cy"] + 5
            head_y = scy - 25
            if seat["status"] == "suspicious":
                head_y += 8
            cv2.circle(frame, (scx, head_y), 12, (200, 210, 220), -1)
            cv2.circle(frame, (scx, head_y), 12, color, 1)
            
            shoulder_y = head_y + 15
            cv2.line(frame, (scx - 22, shoulder_y), (scx + 22, shoulder_y), (180, 190, 200), 3)
            cv2.line(frame, (scx, shoulder_y), (scx, scy + 25), (180, 190, 200), 3)
            
            if seat["status"] == "suspicious":
                cv2.line(frame, (scx - 22, shoulder_y), (scx - 8, shoulder_y + 20), color, 2)
                cv2.line(frame, (scx + 22, shoulder_y), (scx + 6, shoulder_y + 18), color, 2)
                cv2.rectangle(frame, (scx - 8, shoulder_y + 12), (scx + 8, shoulder_y + 24), (230, 230, 230), -1)
                cv2.rectangle(frame, (scx - 8, shoulder_y + 12), (scx + 8, shoulder_y + 24), (0, 0, 255), 1)
            else:
                cv2.line(frame, (scx - 22, shoulder_y), (scx - 28, scy + 20), (160, 170, 180), 2)
                cv2.line(frame, (scx + 22, shoulder_y), (scx + 28, scy + 20), (160, 170, 180), 2)
                
            if seat["status"] == "suspicious":
                status_txt = f"SUSPICIOUS ({seat['suspicious_duration']}s)"
                cv2.putText(frame, status_txt, (bx1 + 10, by2 - 12),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.42, (50, 70, 255), 2, cv2.LINE_AA)
            else:
                cv2.putText(frame, "STATUS: NORMAL", (bx1 + 10, by2 - 12),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.42, (100, 200, 120), 1, cv2.LINE_AA)
                
            bbox = [bx1, by1, bx2, by2]
            detections.append({
                "student_id": seat["student_id"],
                "seat": seat["id"],
                "status": "possible_mobile_usage" if seat["status"] == "suspicious" else "normal",
                "duration": seat["suspicious_duration"],
                "confidence": round(seat["pose_score"], 2),
                "camera_id": self.camera_id,
                "bbox": bbox,
                "timestamp": datetime_iso_str()
            })
            
        # Draw Simulation Mode Banner Top Right
        cv2.rectangle(frame, (self.width - 290, 20), (self.width - 20, 55), (15, 30, 90), -1)
        cv2.rectangle(frame, (self.width - 290, 20), (self.width - 20, 55), (0, 150, 255), 1)
        cv2.putText(frame, f"DEMO MODE - {self.camera_id}", (self.width - 275, 43),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 210, 255), 2, cv2.LINE_AA)
                    
        return frame, detections, self.seats

def datetime_iso_str():
    return time.strftime("%Y-%m-%dT%H:%M:%S")

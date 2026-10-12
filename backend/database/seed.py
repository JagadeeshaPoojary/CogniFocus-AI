import sys
import os
import sqlite3
import datetime
import cv2
import numpy as np
from werkzeug.security import generate_password_hash

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import get_db_connection, init_db

def create_sample_evidence_image(camera_id, student_id, seat_id):
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    ev_dir = os.path.join(root_dir, "backend", "evidence", camera_id)
    os.makedirs(ev_dir, exist_ok=True)
    
    filename = f"{camera_id}_{student_id.replace('-', '')}_sample.jpg"
    filepath = os.path.join(ev_dir, filename)
    
    # Generate sample evidence frame with overlay
    img = np.ones((360, 480, 3), dtype=np.uint8) * 30
    cv2.rectangle(img, (80, 40), (400, 280), (10, 15, 60), -1)
    cv2.rectangle(img, (80, 40), (400, 280), (0, 0, 255), 2)
    
    # Head & torso figure
    cv2.circle(img, (240, 110), 30, (200, 210, 220), -1)
    cv2.circle(img, (240, 110), 30, (0, 0, 255), 2)
    cv2.line(img, (240, 140), (240, 230), (180, 190, 200), 4)
    cv2.rectangle(img, (225, 170), (255, 200), (230, 230, 230), -1)
    cv2.rectangle(img, (225, 170), (255, 200), (0, 0, 255), 1)
    
    # Banner
    cv2.rectangle(img, (0, 325), (480, 360), (15, 20, 30), -1)
    cv2.rectangle(img, (0, 325), (480, 360), (0, 0, 255), 1)
    cv2.putText(img, f"CONFIRMED EVIDENCE | {camera_id} | {seat_id} ({student_id})", (10, 348),
                cv2.FONT_HERSHEY_SIMPLEX, 0.42, (0, 210, 255), 1, cv2.LINE_AA)
                
    cv2.imwrite(filepath, img)
    return f"/evidence/{camera_id}/{filename}"

def seed_db():
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    # Seed Admin & Teacher users
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO users (email, password_hash, role, name)
            VALUES (?, ?, ?, ?)
        ''', ('admin@classroom.com', generate_password_hash('admin123'), 'ADMIN', 'System Admin'))
        cursor.execute('''
            INSERT INTO users (email, password_hash, role, name)
            VALUES (?, ?, ?, ?)
        ''', ('teacher@classroom.com', generate_password_hash('teacher123'), 'TEACHER', 'Prof. Sarah Jenkins'))

    # Seed Teacher Classroom Assignments
    cursor.execute("SELECT id FROM users WHERE email = 'teacher@classroom.com'")
    teacher_row = cursor.fetchone()
    if teacher_row:
        t_id = teacher_row['id']
        cursor.execute("INSERT OR IGNORE INTO teacher_classroom_assignments (teacher_id, classroom_id) VALUES (?, ?)", (t_id, 'CSE-301'))
        cursor.execute("INSERT OR IGNORE INTO teacher_classroom_assignments (teacher_id, classroom_id) VALUES (?, ?)", (t_id, 'CSE-302'))

    # Seed Classrooms (CSE-301 & CSE-302)
    cursor.execute("SELECT id FROM classrooms WHERE id = 'CSE-301'")
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO classrooms (id, name, code, rows, columns, camera_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('CSE-301', 'Computer Science Hall 301', 'CSE301', 4, 3, 'CAM001'))

        # Seed Seats B1 to B12 for CSE-301
        seat_num = 1
        for r in range(1, 5):
            for c in range(1, 4):
                seat_id = f"B{seat_num}"
                student_id = f"STU-00{seat_num}" if seat_num < 10 else f"STU-0{seat_num}"
                cursor.execute('''
                    INSERT INTO seats (id, classroom_id, seat_label, row_idx, col_idx, status, student_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (seat_id, 'CSE-301', seat_id, r, c, 'normal', student_id))
                seat_num += 1

    cursor.execute("SELECT id FROM classrooms WHERE id = 'CSE-302'")
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO classrooms (id, name, code, rows, columns, camera_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', ('CSE-302', 'Computer Science Hall 302', 'CSE302', 4, 3, 'CAM003'))

        # Seed Seats C1 to C12 for CSE-302
        seat_num = 1
        for r in range(1, 5):
            for c in range(1, 4):
                seat_id = f"C{seat_num}"
                student_id = f"STU-10{seat_num}" if seat_num < 10 else f"STU-1{seat_num}"
                cursor.execute('''
                    INSERT INTO seats (id, classroom_id, seat_label, row_idx, col_idx, status, student_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (seat_id, 'CSE-302', seat_id, r, c, 'normal', student_id))
                seat_num += 1

    # Ensure classroom code is CSE301 for CSE-301
    cursor.execute("UPDATE classrooms SET code = 'CSE301' WHERE id = 'CSE-301'")

    # Seed Cameras for CSE-301 and CSE-302
    cams = [
        ('CAM001', 'Classroom 301 Front Camera 1', 'CSE-301', '0', 'Online', 28),
        ('CAM002', 'Classroom 301 Rear Camera 2', 'CSE-301', '1', 'Online', 24),
        ('CAM003', 'Classroom 302 Front Camera 3', 'CSE-302', '2', 'Online', 28),
        ('CAM004', 'Classroom 302 Rear Camera 4', 'CSE-302', '3', 'Online', 24),
    ]
    for c in cams:
        cursor.execute("SELECT id FROM cameras WHERE id = ?", (c[0],))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO cameras (id, name, classroom_id, source, status, fps)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', c)
        else:
            cursor.execute('''
                UPDATE cameras SET classroom_id = ? WHERE id = ?
            ''', (c[2], c[0]))

    # Seed Configuration
    cursor.execute("SELECT COUNT(*) FROM configurations")
    if cursor.fetchone()[0] == 0:
        configs = [
            ('camera_id', 'CAM001'),
            ('camera_source', '0'),
            ('confidence', '0.5'),
            ('alert_time', '10'),
            ('alert_cooldown', '30'),
            ('dashboard_width', '400'),
            ('beep_frequency', '1000'),
            ('beep_duration', '500'),
            ('model_type', 'yolov8n-pose.pt'),
            ('simulation_mode', 'false')
        ]
        cursor.executemany("INSERT INTO configurations (key, value) VALUES (?, ?)", configs)

    # Seed Sample Alerts with VALID Evidence File Paths
    cursor.execute("SELECT COUNT(*) FROM alerts")
    if cursor.fetchone()[0] == 0:
        now = datetime.datetime.now()
        
        sa_b5_ev = create_sample_evidence_image('CAM001', 'STU-005', 'B5')
        sa_b8_ev = create_sample_evidence_image('CAM001', 'STU-008', 'B8')
        sa_b2_ev = create_sample_evidence_image('CAM001', 'STU-002', 'B2')
        sa_b11_ev = create_sample_evidence_image('CAM001', 'STU-011', 'B11')

        sample_alerts = [
            ('CSE-301', 'STU-005', 'B5', 'CAM001', 'Possible Mobile Usage', 0.87, 38, 'Active', 'High', sa_b5_ev, (now - datetime.timedelta(minutes=15)).isoformat()),
            ('CSE-301', 'STU-008', 'B8', 'CAM001', 'Suspicious Posture', 0.79, 45, 'Active', 'Medium', sa_b8_ev, (now - datetime.timedelta(minutes=30)).isoformat()),
            ('CSE-301', 'STU-002', 'B2', 'CAM001', 'Head Drop / Low Posture', 0.82, 22, 'Acknowledged', 'Low', sa_b2_ev, (now - datetime.timedelta(hours=2)).isoformat()),
            ('CSE-301', 'STU-011', 'B11', 'CAM001', 'Possible Mobile Usage', 0.91, 55, 'Resolved', 'High', sa_b11_ev, (now - datetime.timedelta(hours=4)).isoformat()),
        ]
        for sa in sample_alerts:
            cursor.execute('''
                INSERT INTO alerts (classroom_id, student_id, seat_id, camera_id, alert_type, confidence, duration, status, severity, evidence_image, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', sa)

    cursor.execute("UPDATE alerts SET classroom_id = 'CSE-301' WHERE (classroom_id IS NULL OR classroom_id = '') AND camera_id IN ('CAM001', 'CAM002')")
    cursor.execute("UPDATE alerts SET classroom_id = 'CSE-302' WHERE (classroom_id IS NULL OR classroom_id = '') AND camera_id IN ('CAM003', 'CAM004')")

    conn.commit()
    conn.close()
    print("Database successfully initialized and seeded with real evidence image files!")

if __name__ == '__main__':
    seed_db()

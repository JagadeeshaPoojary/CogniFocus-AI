import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'classroom_monitoring.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('ADMIN', 'TEACHER')),
            name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Classrooms table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS classrooms (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            code TEXT UNIQUE NOT NULL,
            rows INTEGER NOT NULL DEFAULT 4,
            columns INTEGER NOT NULL DEFAULT 3,
            camera_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Seats table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS seats (
            id TEXT PRIMARY KEY,
            classroom_id TEXT NOT NULL,
            seat_label TEXT NOT NULL,
            row_idx INTEGER NOT NULL,
            col_idx INTEGER NOT NULL,
            status TEXT DEFAULT 'normal',
            student_id TEXT,
            FOREIGN KEY (classroom_id) REFERENCES classrooms (id) ON DELETE CASCADE
        )
    ''')

    # Cameras table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cameras (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            classroom_id TEXT,
            source TEXT NOT NULL DEFAULT '0',
            status TEXT DEFAULT 'Online',
            fps INTEGER DEFAULT 28,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Monitoring sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monitoring_sessions (
            id TEXT PRIMARY KEY,
            classroom_id TEXT NOT NULL,
            camera_id TEXT NOT NULL,
            teacher_id TEXT,
            start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            end_time TIMESTAMP,
            status TEXT DEFAULT 'ACTIVE'
        )
    ''')

    # Teacher monitoring sessions table (Section 28)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teacher_monitoring_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            classroom_id TEXT NOT NULL,
            classroom_code TEXT NOT NULL,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            stopped_at TIMESTAMP,
            status TEXT DEFAULT 'ACTIVE'
        )
    ''')

    # Teacher classroom assignments / history table (Section 12 & 28)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teacher_classroom_assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            classroom_id TEXT NOT NULL,
            assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(teacher_id, classroom_id)
        )
    ''')

    # Detections table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            student_id TEXT NOT NULL,
            seat_id TEXT NOT NULL,
            pose_score REAL DEFAULT 0.0,
            phone_score REAL DEFAULT 0.0,
            is_suspicious INTEGER DEFAULT 0,
            duration INTEGER DEFAULT 0,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Alerts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            classroom_id TEXT,
            student_id TEXT NOT NULL,
            seat_id TEXT NOT NULL,
            camera_id TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            confidence REAL NOT NULL,
            duration INTEGER NOT NULL,
            status TEXT DEFAULT 'Active',
            severity TEXT DEFAULT 'High',
            evidence_image TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Configurations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS configurations (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')

    # Notification logs table (Section 13)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notification_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_id INTEGER,
            recipient_id INTEGER,
            channel TEXT NOT NULL,
            recipient TEXT NOT NULL,
            status TEXT NOT NULL,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            error_message TEXT
        )
    ''')

    # Teacher Web Push Subscriptions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teacher_push_subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            endpoint TEXT UNIQUE NOT NULL,
            p256dh TEXT NOT NULL,
            auth TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(teacher_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')

    # Migrate columns if missing
    cursor.execute("PRAGMA table_info(alerts)")
    columns = [row[1] for row in cursor.fetchall()]
    if 'evidence_image' not in columns:
        cursor.execute("ALTER TABLE alerts ADD COLUMN evidence_image TEXT")
    if 'classroom_id' not in columns:
        cursor.execute("ALTER TABLE alerts ADD COLUMN classroom_id TEXT")

    cursor.execute("PRAGMA table_info(users)")
    u_cols = [row[1] for row in cursor.fetchall()]
    if 'notification_email' not in u_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN notification_email TEXT")
    if 'notification_phone' not in u_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN notification_phone TEXT")
    if 'email_notifications_enabled' not in u_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN email_notifications_enabled INTEGER DEFAULT 1")
    if 'sms_notifications_enabled' not in u_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN sms_notifications_enabled INTEGER DEFAULT 1")

    conn.commit()
    conn.close()


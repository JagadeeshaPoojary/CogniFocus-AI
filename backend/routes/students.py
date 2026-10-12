from flask import Blueprint, jsonify
from database.db import get_db_connection

students_bp = Blueprint('students', __name__)

@students_bp.route('', methods=['GET'])
def get_students():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.student_id, s.id as seat_id, s.classroom_id,
               COUNT(a.id) as total_alerts,
               COALESCE(SUM(a.duration), 0) as total_suspicious_duration,
               MAX(a.timestamp) as last_detected
        FROM seats s
        LEFT JOIN alerts a ON s.student_id = a.student_id
        GROUP BY s.student_id
        ORDER BY total_alerts DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    
    students = []
    for r in rows:
        students.append({
            "student_id": r['student_id'] or f"STU-{r['seat_id']}",
            "seat": r['seat_id'],
            "classroom_id": r['classroom_id'],
            "total_alerts": r['total_alerts'],
            "total_suspicious_duration": r['total_suspicious_duration'],
            "last_detected": r['last_detected'] or "N/A",
            "risk_level": "High" if r['total_alerts'] > 3 else ("Medium" if r['total_alerts'] > 0 else "Low")
        })
        
    return jsonify({"success": True, "data": students})

@students_bp.route('/<student_id>', methods=['GET'])
def get_student_details(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT * FROM alerts
        WHERE student_id = ?
        ORDER BY id DESC
    ''', (student_id,))
    alert_rows = cursor.fetchall()
    
    cursor.execute('''
        SELECT * FROM seats WHERE student_id = ?
    ''', (student_id,))
    seat_row = cursor.fetchone()
    conn.close()
    
    history = []
    for a in alert_rows:
        history.append({
            "id": a['id'],
            "seat": a['seat_id'],
            "camera_id": a['camera_id'],
            "alert_type": a['alert_type'],
            "confidence": a['confidence'],
            "duration": a['duration'],
            "status": a['status'],
            "timestamp": a['timestamp']
        })
        
    seat_info = seat_row['id'] if seat_row else "Unassigned"
    
    return jsonify({
        "success": True,
        "student": {
            "student_id": student_id,
            "seat": seat_info,
            "total_alerts": len(history),
            "history": history
        }
    })

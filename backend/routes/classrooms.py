from flask import Blueprint, request, jsonify
from database.db import get_db_connection

classrooms_bp = Blueprint('classrooms', __name__)

@classrooms_bp.route('', methods=['GET'])
def get_classrooms():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM classrooms ORDER BY created_at DESC")
    rows = cursor.fetchall()
    conn.close()
    
    classrooms = []
    for r in rows:
        classrooms.append({
            "id": r['id'],
            "name": r['name'],
            "code": r['code'],
            "rows": r['rows'],
            "columns": r['columns'],
            "camera_id": r['camera_id'],
            "created_at": r['created_at']
        })
    return jsonify({"success": True, "data": classrooms})

@classrooms_bp.route('', methods=['POST'])
def create_classroom():
    data = request.get_json() or {}
    c_id = data.get('id', '').strip().upper()
    name = data.get('name', '').strip()
    code = data.get('code', '').strip().upper()
    rows = int(data.get('rows', 4))
    cols = int(data.get('columns', 3))
    camera_id = data.get('camera_id', 'CAM001')
    
    if not c_id or not name or not code:
        return jsonify({"success": False, "message": "Classroom ID, Name, and Access Code are required"}), 400
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check duplicate
    cursor.execute("SELECT id FROM classrooms WHERE id = ? OR code = ?", (c_id, code))
    if cursor.fetchone():
        conn.close()
        return jsonify({"success": False, "message": "Classroom ID or Code already exists"}), 400
        
    cursor.execute('''
        INSERT INTO classrooms (id, name, code, rows, columns, camera_id)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (c_id, name, code, rows, cols, camera_id))
    
    # Generate seats B1 .. B(rows*cols)
    seat_num = 1
    for r in range(1, rows + 1):
        for c in range(1, cols + 1):
            seat_id = f"B{seat_num}"
            student_id = f"STU-00{seat_num}" if seat_num < 10 else f"STU-0{seat_num}"
            cursor.execute('''
                INSERT INTO seats (id, classroom_id, seat_label, row_idx, col_idx, status, student_id)
                VALUES (?, ?, ?, ?, ?, 'normal', ?)
            ''', (seat_id, c_id, seat_id, r, c, student_id))
            seat_num += 1
            
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": f"Classroom {c_id} created successfully!"}), 201

@classrooms_bp.route('/<c_id>', methods=['PUT'])
def update_classroom(c_id):
    data = request.get_json() or {}
    name = data.get('name')
    code = data.get('code')
    rows = data.get('rows')
    cols = data.get('columns')
    camera_id = data.get('camera_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM classrooms WHERE id = ?", (c_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"success": False, "message": "Classroom not found"}), 404
        
    cursor.execute('''
        UPDATE classrooms
        SET name = COALESCE(?, name),
            code = COALESCE(?, code),
            rows = COALESCE(?, rows),
            columns = COALESCE(?, columns),
            camera_id = COALESCE(?, camera_id)
        WHERE id = ?
    ''', (name, code, rows, cols, camera_id, c_id))
    conn.commit()
    conn.close()
    
    return jsonify({"success": True, "message": f"Classroom {c_id} updated successfully"})

@classrooms_bp.route('/<c_id>', methods=['DELETE'])
def delete_classroom(c_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM seats WHERE classroom_id = ?", (c_id,))
    cursor.execute("DELETE FROM classrooms WHERE id = ?", (c_id,))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "message": f"Classroom {c_id} deleted successfully"})

@classrooms_bp.route('/<c_id>/seats', methods=['GET'])
def get_classroom_seats(c_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM seats WHERE classroom_id = ? ORDER BY row_idx, col_idx", (c_id,))
    rows = cursor.fetchall()
    conn.close()
    
    seats = []
    for r in rows:
        seats.append({
            "id": r['id'],
            "label": r['seat_label'],
            "row": r['row_idx'],
            "col": r['col_idx'],
            "status": r['status'],
            "student_id": r['student_id']
        })
    return jsonify({"success": True, "data": seats})

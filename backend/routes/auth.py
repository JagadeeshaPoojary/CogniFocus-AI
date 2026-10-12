from flask import Blueprint, request, jsonify
from werkzeug.security import check_password_hash
import jwt
import datetime
import os
from database.db import get_db_connection

auth_bp = Blueprint('auth', __name__)
SECRET_KEY = "cognifocus_ai_secret_key_prod_demo"

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return jsonify({"success": False, "message": "Invalid email or password"}), 401

    if not check_password_hash(user['password_hash'], password):
        return jsonify({"success": False, "message": "Invalid email or password"}), 401

    token = jwt.encode({
        'user_id': user['id'],
        'email': user['email'],
        'role': user['role'],
        'name': user['name'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, SECRET_KEY, algorithm='HS256')

    return jsonify({
        "success": True,
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user['id'],
            "email": user['email'],
            "role": user['role'],
            "name": user['name']
        }
    }), 200

@auth_bp.route('/me', methods=['GET'])
def get_me():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    token = auth_header.split(' ')[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return jsonify({
            "success": True,
            "user": {
                "id": payload['user_id'],
                "email": payload['email'],
                "role": payload['role'],
                "name": payload['name']
            }
        })
    except jwt.ExpiredSignatureError:
        return jsonify({"success": False, "message": "Token expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"success": False, "message": "Invalid token"}), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    return jsonify({"success": True, "message": "Logged out successfully"})

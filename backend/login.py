# login.py

from flask import Blueprint, request, jsonify
import pyodbc
import jwt
import datetime
from functools import wraps

login_bp = Blueprint('login', __name__)
SECRET_KEY = "your_secret_key"

# =========================
# DB CONNECTION
# =========================
def get_connection():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=10.0.176.120;"
        "DATABASE=erp;"
        "UID=erpadmin;"
        "PWD=erp@admin"
    )

# =========================
# FORMAT DOB (yyyy-mm-dd → ddmmyyyy)
# =========================
def format_dob(dob):
    try:
        dt = datetime.datetime.strptime(dob, "%Y-%m-%d")
        return dt.strftime("%d%m%Y")
    except:
        return None

# =========================
# LOGIN API
# =========================
@login_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.json

        emp_id = data.get('emp_id')
        dob = data.get('dob')
        role = data.get('role')

        print("LOGIN DATA:", emp_id, dob, role)

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT emp_id, role
            FROM lmi_clauses_users
            WHERE 
                LTRIM(RTRIM(emp_id)) = ?
                AND LTRIM(RTRIM(dob)) = ?
                AND UPPER(role) = UPPER(?)
        """, (emp_id, dob, role))

        user = cursor.fetchone()

        if user:
            token = jwt.encode({
                'emp_id': user[0],
                'role': user[1],
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=5)
            }, SECRET_KEY, algorithm='HS256')

            return jsonify({
                "status": "success",
                "token": token,
                "role": user[1]
            })

        return jsonify({"status": "fail", "message": "Invalid credentials"}), 401

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"message": "Server error"}), 500

# =========================
# TOKEN VALIDATION
# =========================
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({'message': 'Token missing'}), 403

        try:
            token = auth_header.split(" ")[1] if " " in auth_header else auth_header

            decoded = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

            request.user = {
                "emp_id": decoded['emp_id'],
                "role": decoded['role']
            }

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expired'}), 401

        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 403

        return f(*args, **kwargs)

    return decorated
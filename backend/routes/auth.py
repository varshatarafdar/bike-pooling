from flask import Blueprint, request, jsonify
from utils.helpers import get_db_connection
import bcrypt
import jwt
import datetime
from config.config import SECRET_KEY

auth_routes = Blueprint('auth', __name__)


# ==============================
# 🔐 REGISTER USER
# ==============================
@auth_routes.route('/register', methods=['POST'])
def register():

    conn = None
    cursor = None

    try:
        data = request.json

        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        phone = data.get("phone", "")
        has_bike = data.get("has_bike", False)

        # validation
        if not name or not email or not password:
            return jsonify({"message": "All fields required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # check existing user
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        existing = cursor.fetchone()

        if existing:
            return jsonify({"message": "Email already registered ❌"}), 400

        # hash password
        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        # insert user
        cursor.execute("""
            INSERT INTO users (name, email, password, phone, has_bike)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, email, hashed_password, phone, has_bike))

        conn.commit()

        return jsonify({
            "message": "User registered successfully ✅"
        })

    except Exception as e:
        print("REGISTER ERROR:", e)
        return jsonify({"message": "Server error"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==============================
# 🔑 LOGIN USER (FIXED CLEAN VERSION)
# ==============================
@auth_routes.route('/login', methods=['POST'])
def login():

    conn = None
    cursor = None

    try:
        data = request.json

        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return jsonify({"message": "Email & Password required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"message": "User not found"}), 404

        # password check
        if not bcrypt.checkpw(
            password.encode('utf-8'),
            user["password"].encode('utf-8')
        ):
            return jsonify({"message": "Invalid password ❌"}), 401

        # JWT token generation
        token = jwt.encode({
            "user_id": user["id"],
            "email": user["email"],
            "exp": datetime.datetime.utcnow() + datetime.timedelta(days=1)
        }, SECRET_KEY, algorithm="HS256")

        # fix python bytes issue
        if isinstance(token, bytes):
            token = token.decode('utf-8')

        return jsonify({
            "message": "Login successful ✅",
            "token": token,
            "user_id": user["id"],
            "name": user["name"],
            "has_bike": user["has_bike"]
        })

    except Exception as e:
        print("LOGIN ERROR:", e)
        return jsonify({"message": "Server error"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
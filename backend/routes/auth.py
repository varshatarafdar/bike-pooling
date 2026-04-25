from flask import Blueprint, request, jsonify
from utils.helpers import get_db_connection, generate_token
import bcrypt
import jwt
import os

auth_routes = Blueprint('auth', __name__)

SECRET_KEY = os.getenv("SECRET_KEY", "bikepool_secret")


# ==============================
# 🔐 REGISTER
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
        has_bike = int(data.get("has_bike", 0))

        if not name or not email or not password:
            return jsonify({
                "status": False,
                "message": "All fields required"
            }), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id FROM users WHERE email=%s", (email,))
        if cursor.fetchone():
            return jsonify({
                "status": False,
                "message": "Email already registered ❌"
            }), 400

        hashed_password = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

        cursor.execute("""
            INSERT INTO users (name, email, password, phone, has_bike)
            VALUES (%s, %s, %s, %s, %s)
        """, (name, email, hashed_password, phone, has_bike))

        conn.commit()

        return jsonify({
            "status": True,
            "message": "User registered successfully ✅"
        })

    except Exception as e:
        print("REGISTER ERROR:", e)
        return jsonify({"status": False, "message": "Server error"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==============================
# 🔑 LOGIN
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

        if not bcrypt.checkpw(
            password.encode('utf-8'),
            user["password"].encode('utf-8')
        ):
            return jsonify({"message": "Invalid password ❌"}), 401

        token = generate_token(user["id"])

        return jsonify({
            "message": "Login successful ✅",
            "token": token,
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "phone": user["phone"],
                "has_bike": user["has_bike"]
            }
        })

    except Exception as e:
        print("LOGIN ERROR:", str(e))
        return jsonify({"message": "Server error"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==============================
# 🔐 TOKEN DECODER (HELPER)
# ==============================
def get_user_from_token(token):
    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return decoded["user_id"]
    except:
        return None


# ==============================
# 👤 GET PROFILE
# ==============================
@auth_routes.route('/profile', methods=['GET'])
def get_profile():

    conn = None
    cursor = None

    try:
        token = request.headers.get("Authorization")

        if not token:
            return jsonify({"message": "Token missing"}), 401

        token = token.split(" ")[1]
        user_id = get_user_from_token(token)

        if not user_id:
            return jsonify({"message": "Invalid token"}), 401

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, name, email, phone, has_bike
            FROM users
            WHERE id=%s
        """, (user_id,))

        user = cursor.fetchone()

        return jsonify(user)

    except Exception as e:
        print("PROFILE ERROR:", e)
        return jsonify({"message": "Server error"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==============================
# ✏️ UPDATE PROFILE
# ==============================
@auth_routes.route('/profile', methods=['PUT'])
def update_profile():

    conn = None
    cursor = None

    try:
        token = request.headers.get("Authorization")

        if not token:
            return jsonify({"message": "Token missing"}), 401

        token = token.split(" ")[1]
        user_id = get_user_from_token(token)

        if not user_id:
            return jsonify({"message": "Invalid token"}), 401

        data = request.json

        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")
        has_bike = data.get("has_bike")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE users
            SET name=%s, email=%s, phone=%s, has_bike=%s
            WHERE id=%s
        """, (name, email, phone, has_bike, user_id))

        conn.commit()

        return jsonify({
            "message": "Profile updated successfully ✅"
        })

    except Exception as e:
        print("UPDATE PROFILE ERROR:", e)
        return jsonify({"message": "Server error"}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
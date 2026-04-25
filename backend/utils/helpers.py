import mysql.connector
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from config.config import DB_CONFIG

# ==============================
# ✅ DATABASE CONNECTION
# ==============================
def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


# ==============================
# 🔐 SECRET KEY
# ==============================
SECRET_KEY = "27cabedd3523a9e2f1c329f6733b2a9119356aebac75c40fc8691c1298eababe"


# ==============================
# 🔐 TOKEN GENERATION
# ==============================
def generate_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(days=1)
    }

    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


# ==============================
# 🔓 TOKEN DECODER (FIXED)
# ==============================
def decode_token(token):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except:
        return None


# ==============================
# 🔒 TOKEN REQUIRED DECORATOR
# ==============================
def token_required(f):

    @wraps(f)
    def decorated(*args, **kwargs):

        token = None

        if "Authorization" in request.headers:
            token = request.headers["Authorization"]

        if not token:
            return jsonify({"message": "Token missing"}), 401

        try:
            if token.startswith("Bearer "):
                token = token.split(" ")[1]

            data = decode_token(token)

            if not data:
                return jsonify({"message": "Invalid token"}), 401

            request.user = data

        except:
            return jsonify({"message": "Token error"}), 401

        return f(*args, **kwargs)

    return decorated
import mysql.connector
from config.config import DB_CONFIG
import jwt
from jwt import encode, decode
import datetime
from functools import wraps
from flask import request, jsonify

# ✅ DATABASE CONNECTION
import mysql.connector

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# ✅ TOKEN GENERATION
def generate_token(user):
    payload = {
        "user_id": user["id"],
        "email": user["email"],
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }

    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


# ✅ TOKEN PROTECTION (FIXED)
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({"message": "Token missing"}), 401

        try:
            # Support: "Bearer <token>"
            token = token.split(" ")[1] if " " in token else token

            decoded = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            request.user = decoded

        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token"}), 401

        return f(*args, **kwargs)

    return decorated
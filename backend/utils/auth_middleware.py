from flask import request, jsonify
from functools import wraps
from utils.helpers import token_required

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):

        token = request.headers.get("Authorization")

        if not token:
            return jsonify({"message": "Token missing"}), 401

        try:
            token = token.split(" ")[1]  # Bearer TOKEN
            data = decode_token(token)
            if not data:
                return jsonify({"message": "Invalid token"}), 401

            request.user_id = data["user_id"]

        except:
            return jsonify({"message": "Token error"}), 401

        return f(*args, **kwargs)

    return decorated
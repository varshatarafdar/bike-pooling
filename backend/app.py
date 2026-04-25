import sys
import os

# ==============================
# 🔗 PROJECT PATH FIX
# ==============================
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
)

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room
from functools import wraps
import jwt
import datetime

# ==============================
# 🔗 CONFIG + DB
# ==============================
from config.config import SECRET_KEY
from config.config import get_db_connection

# ==============================
# 🔗 ROUTES IMPORT
# ==============================
from routes.auth import auth_routes
from routes.rides import ride_routes
from routes.ride_request import request_routes
from routes.match import match_bp

try:
    from routes.booking import booking_routes
except:
    booking_routes = None

# ==============================
# 🚀 APP INIT
# ==============================
app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = SECRET_KEY

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)

# ==============================
# 🔐 JWT AUTH MIDDLEWARE
# ==============================
def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):

        token = request.headers.get("Authorization")

        if not token:
            return jsonify({"status": False, "message": "Token missing"}), 401

        try:
            if "Bearer " in token:
                token = token.split(" ")[1]

            decoded = jwt.decode(
                token,
                app.config['SECRET_KEY'],
                algorithms=["HS256"]
            )

            # ✅ FIXED: only store user_id
            request.user = decoded["user_id"]

        except Exception as e:
            print("JWT ERROR:", e)
            return jsonify({"status": False, "message": "Invalid or expired token"}), 401

        return f(*args, **kwargs)

    return wrapper
# ==============================
# 💳 PAYMENT API (DEMO)
# ==============================
@app.route("/pay", methods=["POST"])
@token_required
def pay():
    data = request.json
    amount = data.get("amount", 50)

    return jsonify({
        "status": True,
        "message": "Payment Successful 💳",
        "amount": amount,
        "time": str(datetime.datetime.utcnow())
    })

# ==============================
# ⭐ RATE RIDE
# ==============================
@app.route("/rate_ride", methods=["POST"])
@token_required
def rate_ride():

    data = request.json
    rating = data.get("rating")
    booking_id = data.get("booking_id")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE bookings 
        SET rating=%s 
        WHERE id=%s
    """, (rating, booking_id))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"status": True, "message": "Rating saved"})

# ==============================
# 🧠 SMART MATCH ENGINE (PLACEHOLDER)
# ==============================
@app.route("/smart_match", methods=["POST"])
@token_required
def smart_match():
    return jsonify({
        "status": True,
        "message": "🤖 Smart Matching Activated",
        "matches": []
    })

# ==============================
# 👤 GET PROFILE
# ==============================
@app.route("/profile", methods=["GET"])
@token_required
def profile():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT id, name, email, phone, has_bike 
        FROM users 
        WHERE id=%s
    """, (request.user,))

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    if not user:
        return jsonify({
            "status": False,
            "message": "User not found"
        }), 404

    # 🔥 IMPORTANT: return clean structure for frontend
    return jsonify(user)
# ==============================
# ✏️ UPDATE PROFILE
# ==============================
@app.route("/profile", methods=["PUT"])
@token_required
def update_profile():

    data = request.json

    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    has_bike = data.get("has_bike")

    if name is None or email is None:
        return jsonify({
            "status": False,
            "message": "Missing required fields"
        }), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE users 
        SET name=%s, email=%s, phone=%s, has_bike=%s
        WHERE id=%s
    """, (
        name,
        email,
        phone,
        has_bike,
        request.user   # ✅ FIXED (no [user_id])
    ))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({
        "status": True,
        "message": "Profile updated successfully ✅"
    })
# ==============================
# 📊 ADMIN STATS
# ==============================
@app.route("/admin_stats")
def admin_stats():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM users")
    users = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM rides")
    rides = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM bookings")
    matches = cursor.fetchone()["total"]

    cursor.execute("SELECT SUM(fare) AS total FROM bookings")
    revenue = cursor.fetchone()["total"] or 0

    cursor.close()
    conn.close()

    return jsonify({
        "status": True,
        "users": users,
        "rides": rides,
        "matches": matches,
        "revenue": revenue
    })

# ==============================
# 🔗 REGISTER BLUEPRINTS
# ==============================
app.register_blueprint(auth_routes, url_prefix="/auth")
app.register_blueprint(ride_routes)
app.register_blueprint(request_routes)
app.register_blueprint(match_bp)

if booking_routes:
    app.register_blueprint(booking_routes)

# ==============================
# 🔌 SOCKET.IO EVENTS
# ==============================
@socketio.on('connect')
def handle_connect():
    print("🔌 Client Connected")

@socketio.on('join_room')
def handle_join(data):
    room = str(data.get("user_id"))
    join_room(room)
    print(f"👤 Joined room: {room}")

@socketio.on('ride_update')
def ride_update(data):
    socketio.emit('ride_update', data, broadcast=True)

@socketio.on('pool_created')
def pool_created(data):
    driver = str(data.get("driver_id"))
    passenger = str(data.get("passenger_id"))

    socketio.emit("pool_created", data, room=driver)
    socketio.emit("pool_created", data, room=passenger)

@socketio.on("chat_message")
def chat(data):
    emit("chat_message", data, broadcast=True)

@socketio.on("location_update")
def location_update(data):
    emit("location_update", data, broadcast=True)

# ==============================
# 🏠 ROOT ROUTE
# ==============================
@app.route('/')
def home():
    return jsonify({
        "status": True,
        "message": "🚲 Bike Pooling System API Running Successfully"
    })

# ==============================
# 🩺 HEALTH CHECK
# ==============================
@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "time": str(datetime.datetime.utcnow())
    })

# ==============================
# ❌ ERROR HANDLING
# ==============================
@app.errorhandler(404)
def not_found(error):
    return jsonify({"status": False, "message": "Route not found"}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({"status": False, "message": "Internal server error"}), 500

# ==============================
# ▶️ RUN SERVER
# ==============================
if __name__ == "__main__":
    socketio.run(
        app,
        debug=True,
        host="0.0.0.0",
        port=5000
    )

    
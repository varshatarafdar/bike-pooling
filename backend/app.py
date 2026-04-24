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
# 🔗 CONFIG
# ==============================
from config.config import SECRET_KEY

# ==============================
# 🔗 ROUTES IMPORT
# ==============================
from routes.auth import auth_routes
from routes.rides import ride_routes
from routes.ride_request import request_routes
from routes.match import match_bp

# optional safe import
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
            return jsonify({"error": "Token missing"}), 401

        try:
            # Accept both formats: Bearer token OR raw token
            if "Bearer " in token:
                token = token.split(" ")[1]

            decoded = jwt.decode(
                token,
                app.config['SECRET_KEY'],
                algorithms=["HS256"]
            )

            request.user = decoded

        except Exception:
            return jsonify({"error": "Invalid or expired token"}), 401

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
        "status": "success",
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

    return jsonify({"message": "Rating saved"})

# ==============================
# 🧠 SMART MATCH ENGINE (HOOK FOR ML)
# ==============================
@app.route("/smart_match", methods=["POST"])
@token_required
def smart_match():

    return jsonify({
        "message": "🤖 Smart Matching Activated",
        "matches": []
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
    return jsonify({"error": "Route not found"}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({"error": "Internal server error"}), 500


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
        "users": users,
        "rides": rides,
        "matches": matches,
        "revenue": revenue
    })
@app.route("/profile")
@token_required
def profile():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT name,email,has_bike FROM users WHERE id=%s",
                   (request.user["user_id"],))

    user = cursor.fetchone()

    cursor.close()
    conn.close()

    return jsonify(user)
@app.route("/update_profile", methods=["POST"])
@token_required
def update_profile():
    name = request.json.get("name")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE users SET name=%s WHERE id=%s",
                   (name, request.user["user_id"]))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message":"updated"})
@app.route("/update_bike", methods=["POST"])
@token_required
def update_bike():
    has_bike = request.json.get("has_bike")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE users SET has_bike=%s WHERE id=%s",
                   (has_bike, request.user["user_id"]))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({"message":"updated"})
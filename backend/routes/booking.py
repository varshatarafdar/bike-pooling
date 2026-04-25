from flask import Blueprint, jsonify, request
from utils.helpers import token_required, get_db_connection

booking_routes = Blueprint('booking', __name__)


# ==============================
# 🚀 GET ACTIVE RIDE
# ==============================
@booking_routes.route('/active_booking', methods=['GET'])
@token_required
def active_booking():

    user_id = request.user['user_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            b.id AS booking_id,
            b.driver_id,
            b.passenger_id,
            b.status,
            b.fare,
            
            d.name AS driver_name,
            d.phone AS driver_phone,
            
            p.name AS passenger_name,
            p.phone AS passenger_phone,

            r.start_location,
            r.destination,
            r.start_lat,
            r.start_lng,
            r.dest_lat,
            r.dest_lng,
            r.time

        FROM bookings b
        JOIN users d ON b.driver_id = d.id
        JOIN users p ON b.passenger_id = p.id
        JOIN rides r ON b.ride_id = r.ride_id
        WHERE (b.driver_id=%s OR b.passenger_id=%s)
        AND b.status IN ('matched','started','accepted','arriving')
        ORDER BY b.id DESC
        LIMIT 1
    """, (user_id, user_id))

    booking = cursor.fetchone()

    cursor.close()
    conn.close()

    if not booking:
        return jsonify({"booking": None})

    return jsonify({"booking": booking})


# ==============================
# 🔄 UPDATE RIDE STATUS
# ==============================
@booking_routes.route('/update_status', methods=['POST'])
@token_required
def update_status():

    data = request.json
    booking_id = data.get("booking_id")
    status = data.get("status")

    # ✅ expanded lifecycle for frontend buttons
    valid_status = ["accepted", "arriving", "started", "completed"]

    if status not in valid_status:
        return jsonify({"message": "Invalid status"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE bookings
        SET status=%s
        WHERE id=%s
    """, (status, booking_id))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({"message": "Status updated"})


# ==============================
# 📜 GET ALL BOOKINGS
# ==============================
@booking_routes.route('/my_bookings', methods=['GET'])
@token_required
def my_bookings():

    user_id = request.user['user_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT 
            b.id AS booking_id,
            b.driver_id,
            b.passenger_id,
            b.status,
            b.fare,

            d.name AS driver_name,
            p.name AS passenger_name,

            r.start_location,
            r.destination,
            r.time

        FROM bookings b
        JOIN users d ON b.driver_id = d.id
        JOIN users p ON b.passenger_id = p.id
        JOIN rides r ON b.ride_id = r.ride_id
        WHERE b.driver_id=%s OR b.passenger_id=%s
        ORDER BY b.id DESC
    """, (user_id, user_id))

    bookings = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({"bookings": bookings})


# ==============================
# ⭐ RATE RIDE
# ==============================
@booking_routes.route('/rate', methods=['POST'])
@token_required
def rate():

    data = request.json

    booking_id = data.get("booking_id")
    rating = data.get("rating")

    if not booking_id or not rating:
        return jsonify({"message": "Missing fields"}), 400

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

    return jsonify({"message": "⭐ Rating submitted"})
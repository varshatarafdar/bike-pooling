from flask import Blueprint, request, jsonify
from utils.helpers import token_required, get_db_connection
from models.ride_model import create_ride, get_matching_rides
from routes.match import find_best_match, calculate_distance

ride_routes = Blueprint('rides', __name__)


# ==============================
# 🚲 ADD RIDE + AUTO MATCH ENGINE
# ==============================
@ride_routes.route('/add_ride', methods=['POST'])
@token_required
def add_ride():

    conn = None
    cursor = None

    try:
        data = request.json
        user_id = request.user['user_id']

        required_fields = [
            "start", "destination",
            "start_lat", "start_lng",
            "dest_lat", "dest_lng",
            "time"
        ]

        for field in required_fields:
            if field not in data:
                return jsonify({"message": f"{field} is required"}), 400

        # ==============================
        # 🚀 CREATE RIDE
        # ==============================
        create_ride(
            user_id,
            data['start'],
            data['destination'],
            data['start_lat'],
            data['start_lng'],
            data['dest_lat'],
            data['dest_lng'],
            data['time']
        )

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # ==============================
        # 🔥 GET LATEST USER RIDE
        # ==============================
        cursor.execute("""
            SELECT r.*, u.has_bike
            FROM rides r
            JOIN users u ON r.user_id = u.id
            WHERE r.user_id=%s
            ORDER BY r.created_at DESC
            LIMIT 1
        """, (user_id,))

        user_ride = cursor.fetchone()

        # ==============================
        # 🔍 FETCH ALL SEARCHING RIDES
        # ==============================
        cursor.execute("""
            SELECT r.*, u.has_bike, u.name
            FROM rides r
            JOIN users u ON r.user_id = u.id
            WHERE r.user_id != %s AND r.status='searching'
        """, (user_id,))

        all_rides = cursor.fetchall()

        # ==============================
        # 🧠 FIND BEST MATCH
        # ==============================
        best_match = find_best_match(user_ride, all_rides)

        if best_match:

            # 🚗 DRIVER / PASSENGER LOGIC
            if user_ride["has_bike"]:
                driver_id = user_id
                passenger_id = best_match["user_id"]
                ride_id = user_ride["ride_id"]
            else:
                driver_id = best_match["user_id"]
                passenger_id = user_id
                ride_id = best_match["ride_id"]

            # 📏 DISTANCE + FARE
            distance = calculate_distance(
                user_ride["start_lat"], user_ride["start_lng"],
                user_ride["dest_lat"], user_ride["dest_lng"]
            )

            fare = round(distance * 10, 2)

            # ==============================
            # 🚀 CREATE BOOKING
            # ==============================
            cursor.execute("""
                INSERT INTO bookings
                (driver_id, passenger_id, ride_id, fare, status)
                VALUES (%s, %s, %s, %s, %s)
            """, (driver_id, passenger_id, ride_id, fare, "matched"))

            # ==============================
            # 🔄 UPDATE RIDE STATUS
            # ==============================
            cursor.execute("""
                UPDATE rides SET status='matched'
                WHERE ride_id IN (%s, %s)
            """, (user_ride["ride_id"], best_match["ride_id"]))

            conn.commit()

            return jsonify({
                "message": "🎉 Match Found Successfully!",
                "status": "matched",
                "driver_id": driver_id,
                "passenger_id": passenger_id,
                "fare": fare
            })

        # ==============================
        # ❌ NO MATCH FOUND
        # ==============================
        return jsonify({
            "message": "🔍 Searching for riders...",
            "status": "searching"
        })

    except Exception as e:
        print("RIDE ERROR:", e)
        return jsonify({
            "message": "Failed to create ride",
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==============================
# 📍 GET LAST RIDE
# ==============================
@ride_routes.route('/my_last_ride', methods=['GET'])
@token_required
def my_last_ride():

    conn = None
    cursor = None

    try:
        user_id = request.user['user_id']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT * FROM rides
            WHERE user_id=%s
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id,))

        ride = cursor.fetchone()

        if not ride:
            return jsonify({"message": "No ride found"}), 404

        return jsonify(ride)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ==============================
# 🔥 GET MATCHES (SMART VIEW)
# ==============================
@ride_routes.route('/my_matches', methods=['GET'])
@token_required
def my_matches():

    conn = None
    cursor = None

    try:
        user_id = request.user['user_id']

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT * FROM rides
            WHERE user_id=%s
            ORDER BY created_at DESC
            LIMIT 1
        """, (user_id,))

        user_ride = cursor.fetchone()

        if not user_ride:
            return jsonify({
                "matches": [],
                "message": "Create a ride first"
            })

        matches = get_matching_rides(
            user_id,
            user_ride["start_lat"],
            user_ride["start_lng"],
            user_ride["dest_lat"],
            user_ride["dest_lng"],
            user_ride["time"]
        )

        return jsonify({
            "matches": matches
        })

    except Exception as e:
        return jsonify({
            "message": "Match error",
            "error": str(e)
        }), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
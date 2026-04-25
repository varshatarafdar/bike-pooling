from flask import Blueprint, request, jsonify
from utils.helpers import get_db_connection
from utils.auth_middleware import token_required
from models.ride_model import calculate_distance
from datetime import datetime

ride_routes = Blueprint('rides', __name__)


# ==============================
# 🚲 ADD RIDE + AUTO MATCH
# ==============================
@ride_routes.route('/add_ride', methods=['POST'])
@token_required
def add_ride():
    try:
        data = request.json

        # ✅ FIXED USER ID ACCESS
        user_id = request.user["user_id"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # ==============================
        # 🚀 INSERT RIDE
        # ==============================
        cursor.execute("""
            INSERT INTO rides 
            (user_id, start_location, destination,
             start_lat, start_lng, dest_lat, dest_lng,
             ride_time, status)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'searching')
        """, (
            user_id,
            data['start'],
            data['destination'],
            float(data['start_lat']),
            float(data['start_lng']),
            float(data['dest_lat']),
            float(data['dest_lng']),
            data['time']
        ))

        conn.commit()
        ride_id = cursor.lastrowid

        # ==============================
        # 🤖 AUTO MATCH TRIGGER
        # ==============================
        match_found = auto_match(user_id, ride_id, conn, cursor)

        return jsonify({
            "message": "Ride Booked Successfully",
            "ride_id": ride_id,
            "match_found": match_found
        })

    except Exception as e:
        print("ADD RIDE ERROR:", e)
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# ==============================
# 🤖 AUTO MATCH FUNCTION
# ==============================
def auto_match(user_id, ride_id, conn, cursor):

    # Get current ride
    cursor.execute("SELECT * FROM rides WHERE ride_id=%s", (ride_id,))
    my_ride = cursor.fetchone()

    if not my_ride:
        return False

    # Get other rides
    cursor.execute("""
        SELECT r.*, u.has_bike
        FROM rides r
        JOIN users u ON r.user_id = u.id
        WHERE r.user_id != %s AND r.status='searching'
    """, (user_id,))

    rides = cursor.fetchall()

    for r in rides:

        # ==============================
        # 📍 DISTANCE CHECK
        # ==============================
        pickup_dist = calculate_distance(
            my_ride["start_lat"], my_ride["start_lng"],
            r["start_lat"], r["start_lng"]
        )

        drop_dist = calculate_distance(
            my_ride["dest_lat"], my_ride["dest_lng"],
            r["dest_lat"], r["dest_lng"]
        )

        # ==============================
        # ⏱ SAFE TIME CHECK (FIXED)
        # ==============================
        try:
            t1 = datetime.strptime(str(my_ride["ride_time"])[:16], "%Y-%m-%d %H:%M")
            t2 = datetime.strptime(str(r["ride_time"])[:16], "%Y-%m-%d %H:%M")

            time_diff = abs((t1 - t2).total_seconds()) / 60

        except:
            time_diff = 9999

        # ==============================
        # 🎯 MATCH CONDITIONS
        # ==============================
        if pickup_dist < 2 and drop_dist < 2 and time_diff <= 15:

            # DRIVER LOGIC
            if r["has_bike"]:
                driver = r["user_id"]
                passenger = user_id
            else:
                driver = user_id
                passenger = r["user_id"]

            # ==============================
            # 💰 FARE (simple logic)
            # ==============================
            fare = round((pickup_dist + drop_dist) * 10, 2)

            # ==============================
            # 🤝 CREATE BOOKING
            # ==============================
            cursor.execute("""
                INSERT INTO bookings 
                (driver_id, passenger_id, ride_id, fare, status)
                VALUES (%s,%s,%s,%s,'matched')
            """, (driver, passenger, ride_id, fare))

            # ==============================
            # 🔄 UPDATE RIDES
            # ==============================
            cursor.execute("""
                UPDATE rides SET status='matched'
                WHERE ride_id IN (%s,%s)
            """, (my_ride["ride_id"], r["ride_id"]))

            conn.commit()
            return True

    return False


# ==============================
# 📍 GET MATCHES (SAFE)
# ==============================
@ride_routes.route('/my_matches', methods=['GET'])
@token_required
def my_matches():
    try:
        user_id = request.user["user_id"]

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # get my ride
        cursor.execute("""
            SELECT * FROM rides 
            WHERE user_id=%s AND status='searching'
            ORDER BY created_at DESC LIMIT 1
        """, (user_id,))

        my_ride = cursor.fetchone()

        if not my_ride:
            return jsonify({"matches": []})

        # other rides
        cursor.execute("""
            SELECT r.*, u.name, u.phone, u.has_bike
            FROM rides r
            JOIN users u ON r.user_id = u.id
            WHERE r.user_id != %s AND r.status='searching'
        """, (user_id,))

        rides = cursor.fetchall()

        matches = []

        for r in rides:

            pickup_dist = calculate_distance(
                my_ride["start_lat"], my_ride["start_lng"],
                r["start_lat"], r["start_lng"]
            )

            drop_dist = calculate_distance(
                my_ride["dest_lat"], my_ride["dest_lng"],
                r["dest_lat"], r["dest_lng"]
            )

            # TIME FILTER (±15 min)
            t1 = str(my_ride["ride_time"])[:5]
            t2 = str(r["ride_time"])[:5]

            time_diff = abs(
                (datetime.strptime(t1, "%H:%M") -
                 datetime.strptime(t2, "%H:%M")
                ).total_seconds() / 60
            )

            if pickup_dist <= 2 and drop_dist <= 2 and time_diff <= 15:
                matches.append({
                    "ride_id": r["ride_id"],
                    "user_id": r["user_id"],
                    "name": r["name"],
                    "phone": r["phone"],
                    "has_bike": r["has_bike"],
                    "start": r["start_location"],
                    "destination": r["destination"],
                    "pickup_distance": pickup_dist,
                    "drop_distance": drop_dist,
                    "time": r["ride_time"]
                })

        return jsonify({"matches": matches})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()
   
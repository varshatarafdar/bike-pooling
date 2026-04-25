from flask import Blueprint, request, jsonify
from math import radians, cos, sin, sqrt, atan2
from utils.helpers import get_db_connection, token_required
from datetime import datetime

match_bp = Blueprint('match', __name__)


# ==============================
# 📏 DISTANCE (HAVERSINE)
# ==============================
def calculate_distance(lat1, lon1, lat2, lon2):

    R = 6371.0

    lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


# ==============================
# ⏱ TIME CHECK (±15 MIN)
# ==============================
def time_diff(t1, t2):

    try:
        fmt = "%H:%M"

        d1 = datetime.strptime(t1[:5], fmt)
        d2 = datetime.strptime(t2[:5], fmt)

        return abs((d1 - d2).total_seconds() / 60)

    except:
        return 9999


# ==============================
# 🧠 AUTO MATCH ENGINE (1-1)
# ==============================
@match_bp.route('/auto_match', methods=['POST'])
@token_required
def auto_match():

    user_id = request.user["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:

        # 🔥 latest ride
        cursor.execute("""
            SELECT r.*, u.has_bike
            FROM rides r
            JOIN users u ON r.user_id = u.id
            WHERE r.user_id=%s AND r.status='searching'
            ORDER BY r.id DESC
            LIMIT 1
        """, (user_id,))

        user_ride = cursor.fetchone()

        if not user_ride:
            return jsonify({"status": "no_ride"})

        # 🔍 other rides
        cursor.execute("""
            SELECT r.*, u.has_bike, u.name
            FROM rides r
            JOIN users u ON r.user_id = u.id
            WHERE r.user_id != %s AND r.status='searching'
        """, (user_id,))

        rides = cursor.fetchall()

        best = None
        best_score = 99999

        for r in rides:

            if time_diff(user_ride["ride_time"], r["ride_time"]) > 15:
                continue

            if not (user_ride["has_bike"] or r["has_bike"]):
                continue

            start_dist = calculate_distance(
                user_ride["start_lat"], user_ride["start_lng"],
                r["start_lat"], r["start_lng"]
            )

            dest_dist = calculate_distance(
                user_ride["dest_lat"], user_ride["dest_lng"],
                r["dest_lat"], r["dest_lng"]
            )

            if start_dist > 2 or dest_dist > 2:
                continue

            score = start_dist + dest_dist

            if r["has_bike"]:
                score -= 0.3

            if score < best_score:
                best_score = score
                best = r

        if not best:
            return jsonify({"status": "waiting"})

        # 🚗 assign roles
        if user_ride["has_bike"]:
            driver_id = user_id
            passenger_id = best["user_id"]
        else:
            driver_id = best["user_id"]
            passenger_id = user_id

        # 💰 fare
        fare = round(best_score * 10, 2)

        # 💾 booking
        cursor.execute("""
            INSERT INTO bookings
            (driver_id, passenger_id, ride_id, fare, status)
            VALUES (%s,%s,%s,%s,'matched')
        """, (driver_id, passenger_id, user_ride["id"], fare))

        # 🔄 update rides
        cursor.execute("""
            UPDATE rides
            SET status='matched'
            WHERE id IN (%s,%s)
        """, (user_ride["id"], best["id"]))

        conn.commit()

        return jsonify({
            "status": "matched",
            "driver_id": driver_id,
            "passenger_id": passenger_id,
            "fare": fare
        })

    except Exception as e:
        return jsonify({"error": str(e)})

    finally:
        cursor.close()
        conn.close()


# ==============================
# 🔄 POLLING CHECK (Dashboard)
# ==============================
@match_bp.route('/check_match', methods=['GET'])
@token_required
def check_match():

    user_id = request.user["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM bookings
        WHERE driver_id=%s OR passenger_id=%s
        ORDER BY id DESC
        LIMIT 1
    """, (user_id, user_id))

    booking = cursor.fetchone()

    cursor.close()
    conn.close()

    return jsonify({
        "match_found": bool(booking),
        "booking": booking
    })


# ==============================
# 📍 LIVE MATCH LIST (2km + time filter)
# ==============================
@match_bp.route('/my_matches', methods=['GET'])
@token_required
def my_matches():

    user_id = request.user["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT r.*, u.name, u.has_bike
        FROM rides r
        JOIN users u ON r.user_id = u.id
        WHERE r.user_id != %s AND r.status='searching'
    """, (user_id,))

    rides = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({"matches": rides})
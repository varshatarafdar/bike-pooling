from flask import Blueprint, request, jsonify
from math import radians, cos, sin, sqrt, atan2
from utils.helpers import get_db_connection
from datetime import datetime

match_bp = Blueprint('match', __name__)


# ==============================
# 📏 DISTANCE (HAVERSINE FORMULA)
# ==============================
def calculate_distance(lat1, lon1, lat2, lon2):

    R = 6371.0

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


# ==============================
# ⏱ SAFE TIME DIFFERENCE
# ==============================
def time_diff(t1, t2):

    try:
        fmt = "%H:%M"

        if len(t1) > 5:
            t1 = t1[:5]
        if len(t2) > 5:
            t2 = t2[:5]

        d1 = datetime.strptime(t1, fmt)
        d2 = datetime.strptime(t2, fmt)

        return abs((d1 - d2).total_seconds() / 60)

    except:
        return 9999  # invalid time → ignore match


# ==============================
# 🔍 SMART MATCH ENGINE
# ==============================
def find_best_match(user_ride, all_rides):

    best_match = None
    best_score = float("inf")

    for ride in all_rides:

        # 📍 START DISTANCE
        start_dist = calculate_distance(
            user_ride["start_lat"], user_ride["start_lng"],
            ride["start_lat"], ride["start_lng"]
        )

        # 📍 DESTINATION DISTANCE
        dest_dist = calculate_distance(
            user_ride["dest_lat"], user_ride["dest_lng"],
            ride["dest_lat"], ride["dest_lng"]
        )

        # ⏱ TIME FILTER (±30 min)
        if time_diff(user_ride["time"], ride["time"]) > 30:
            continue

        # 🚲 BIKE CONDITION (at least one must have bike)
        if not (user_ride["has_bike"] or ride["has_bike"]):
            continue

        # 📏 STRICT MATCH RULE (2 KM)
        if start_dist > 2 or dest_dist > 2:
            continue

        # 🎯 SCORING SYSTEM
        score = start_dist + dest_dist

        # ⭐ PRIORITY BOOST: bike owner preferred
        if ride["has_bike"]:
            score -= 0.3

        if score < best_score:
            best_score = score
            best_match = ride

    return best_match


# ==============================
# 🚀 AUTO MATCH + POOL CREATION
# ==============================
@match_bp.route('/auto_match', methods=['POST'])
def auto_match():

    data = request.json
    user_id = data.get("user_id")

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # ==============================
    # 🔥 GET USER LATEST RIDE
    # ==============================
    cursor.execute("""
        SELECT r.*, u.has_bike
        FROM rides r
        JOIN users u ON r.user_id = u.id
        WHERE r.user_id=%s AND r.status='searching'
        ORDER BY r.created_at DESC
        LIMIT 1
    """, (user_id,))

    user_ride = cursor.fetchone()

    if not user_ride:
        return jsonify({"message": "No active ride found"})

    # 🔒 PREVENT DUPLICATE BOOKING
    cursor.execute("""
        SELECT * FROM bookings
        WHERE driver_id=%s OR passenger_id=%s
    """, (user_id, user_id))

    if cursor.fetchone():
        return jsonify({"message": "Already matched"})

    # ==============================
    # 🔍 FETCH OTHER RIDES
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

    if not best_match:
        return jsonify({"message": "No match found"})

    # ==============================
    # 🚗 ASSIGN DRIVER / PASSENGER
    # ==============================
    if user_ride["has_bike"]:
        driver_id = user_id
        passenger_id = best_match["user_id"]
        ride_id = user_ride["ride_id"]
    else:
        driver_id = best_match["user_id"]
        passenger_id = user_id
        ride_id = best_match["ride_id"]

    # ==============================
    # 💰 FARE CALCULATION
    # ==============================
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

    cursor.close()
    conn.close()

    return jsonify({
        "message": "🎉 Pool Created Successfully",
        "driver_id": driver_id,
        "passenger_id": passenger_id,
        "fare": fare
    })


# ==============================
# 🔔 POOL STATUS CHECK
# ==============================
@match_bp.route('/pool_status/<int:user_id>', methods=['GET'])
def pool_status(user_id):

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT b.*,
               d.name AS driver_name,
               p.name AS passenger_name
        FROM bookings b
        JOIN users d ON b.driver_id = d.id
        JOIN users p ON b.passenger_id = p.id
        WHERE b.driver_id=%s OR b.passenger_id=%s
        ORDER BY b.created_at DESC
        LIMIT 1
    """, (user_id, user_id))

    booking = cursor.fetchone()

    cursor.close()
    conn.close()

    if not booking:
        return jsonify({"status": "waiting"})

    return jsonify({
        "status": "matched",
        "booking": booking
    })
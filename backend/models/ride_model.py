from utils.helpers import get_db_connection
from math import radians, cos, sin, sqrt, atan2
from datetime import datetime


# ==============================
# 📏 DISTANCE CALCULATION (KM)
# ==============================
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371.0

    lat1 = radians(float(lat1))
    lon1 = radians(float(lon1))
    lat2 = radians(float(lat2))
    lon2 = radians(float(lon2))

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


# ==============================
# 🚲 CREATE RIDE (SAFE VERSION)
# ==============================
def create_ride(user_id, start, dest, slat, slng, dlat, dlng, time):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        query = """
        INSERT INTO rides 
        (user_id, start_location, destination, start_lat, start_lng, dest_lat, dest_lng, time, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        cursor.execute(query, (
            user_id,
            start,
            dest,
            float(slat),
            float(slng),
            float(dlat),
            float(dlng),
            time,
            "searching"
        ))

        conn.commit()

    except Exception as e:
        print("CREATE RIDE ERROR:", e)

    finally:
        cursor.close()
        conn.close()


# ==============================
# ⏱ TIME MATCH (±15 MIN SAFE)
# ==============================
def is_time_close(t1, t2):
    try:
        fmt = "%H:%M"

        if not t1 or not t2:
            return False

        time1 = datetime.strptime(t1, fmt)
        time2 = datetime.strptime(t2, fmt)

        diff = abs((time1 - time2).total_seconds()) / 60
        return diff <= 15

    except Exception:
        return False


# ==============================
# 🔍 SMART MATCH RIDES
# ==============================
def get_matching_rides(user_id, start_lat, start_lng, dest_lat, dest_lng, time):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        query = """
        SELECT r.*, u.name, u.has_bike
        FROM rides r
        JOIN users u ON r.user_id = u.id
        WHERE r.user_id != %s 
        AND r.status='searching'
        """

        cursor.execute(query, (user_id,))
        rides = cursor.fetchall()

        matches = []

        for ride in rides:

            # skip bad data safely
            if not ride.get("start_lat") or not ride.get("dest_lat"):
                continue

            start_dist = calculate_distance(
                start_lat, start_lng,
                ride["start_lat"], ride["start_lng"]
            )

            dest_dist = calculate_distance(
                dest_lat, dest_lng,
                ride["dest_lat"], ride["dest_lng"]
            )

            time_match = is_time_close(time, ride["time"])

            # MAIN RULE (UNCHANGED LOGIC)
            if start_dist <= 2 and dest_dist <= 2 and time_match:

                score = start_dist + dest_dist

                matches.append({
                    "ride_id": ride["ride_id"],
                    "user_id": ride["user_id"],
                    "name": ride["name"],
                    "start": ride["start_location"],
                    "destination": ride["destination"],
                    "time": ride["time"],
                    "distance": round(start_dist, 2),
                    "dest_distance": round(dest_dist, 2),
                    "score": round(score, 2),
                    "has_bike": ride["has_bike"]
                })

        matches.sort(key=lambda x: x["score"])
        return matches

    finally:
        cursor.close()
        conn.close()


# ==============================
# 📄 GET ALL RIDES
# ==============================
def get_all_rides():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
        SELECT r.*, u.name AS driver_name, u.has_bike
        FROM rides r
        JOIN users u ON r.user_id = u.id
        WHERE r.status='searching'
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        conn.close()


# ==============================
# 🔍 GET RIDE BY ID
# ==============================
def get_ride_by_id(ride_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM rides WHERE ride_id=%s", (ride_id,))
        return cursor.fetchone()

    finally:
        cursor.close()
        conn.close()


# ==============================
# 🔄 UPDATE STATUS
# ==============================
def update_ride_status(ride_id, status):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "UPDATE rides SET status=%s WHERE ride_id=%s",
            (status, ride_id)
        )
        conn.commit()

    finally:
        cursor.close()
        conn.close()
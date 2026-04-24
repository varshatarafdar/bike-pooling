from utils.helpers import get_db_connection
from math import radians, cos, sin, sqrt, atan2


# ==============================
# 📏 DISTANCE CALCULATION (KM)
# ==============================
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6373.0

    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


# ==============================
# 🚲 CREATE RIDE
# ==============================
def create_ride(user_id, start, dest, slat, slng, dlat, dlng, time):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    INSERT INTO rides 
    (user_id, start_location, destination, start_lat, start_lng, dest_lat, dest_lng, time)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    cursor.execute(query, (user_id, start, dest, slat, slng, dlat, dlng, time))
    conn.commit()

    cursor.close()
    conn.close()


# ==============================
# 🔍 SMART MATCH RIDES (MAIN LOGIC)
# ==============================
def get_matching_rides(user_id, start_lat, start_lng, dest_lat, dest_lng, time):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # 🔥 GET OTHER USERS RIDES
    query = """
    SELECT r.*, u.name, u.has_bike
    FROM rides r
    JOIN users u ON r.user_id = u.id
    WHERE r.user_id != %s AND r.status='available'
    """

    cursor.execute(query, (user_id,))
    rides = cursor.fetchall()

    matches = []

    for ride in rides:

        start_dist = calculate_distance(
            start_lat, start_lng,
            ride["start_lat"], ride["start_lng"]
        )

        dest_dist = calculate_distance(
            dest_lat, dest_lng,
            ride["dest_lat"], ride["dest_lng"]
        )

        # ⏱ TIME MATCH (allow small flexibility)
        time_match = ride["time"] == time

        # 🚲 BIKE LOGIC
        bike_match = ride["has_bike"]  # at least one rider must have bike

        # 🎯 FINAL MATCH RULE
        if start_dist < 3 and dest_dist < 3 and time_match and bike_match:
            matches.append({
                "ride_id": ride["ride_id"],
                "user_id": ride["user_id"],
                "name": ride["name"],
                "start": ride["start_location"],
                "destination": ride["destination"],
                "time": ride["time"],
                "distance_score": round(start_dist + dest_dist, 2),
                "has_bike": ride["has_bike"]
            })

    # 🔥 SORT BEST MATCH FIRST
    matches.sort(key=lambda x: x["distance_score"])

    cursor.close()
    conn.close()

    return matches


# ==============================
# 📄 GET ALL RIDES (FALLBACK)
# ==============================
def get_all_rides():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT r.*, u.name AS driver_name
    FROM rides r
    JOIN users u ON r.user_id = u.id
    WHERE r.status='available'
    """

    cursor.execute(query)
    rides = cursor.fetchall()

    cursor.close()
    conn.close()

    return rides


# ==============================
# 🔍 GET SINGLE RIDE
# ==============================
def get_ride_by_id(ride_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM rides WHERE ride_id=%s", (ride_id,))
    ride = cursor.fetchone()

    cursor.close()
    conn.close()

    return ride


# ==============================
# 🔄 UPDATE RIDE STATUS
# ==============================
def update_ride_status(ride_id, status):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE rides SET status=%s WHERE ride_id=%s",
        (status, ride_id)
    )

    conn.commit()
    cursor.close()
    conn.close()
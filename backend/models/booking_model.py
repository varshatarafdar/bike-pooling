from utils.helpers import get_db_connection


# ==============================
# 📦 CREATE BOOKING
# ==============================
def create_booking(driver_id, passenger_id, ride_id, fare):
    conn = get_db_connection()
    cursor = conn.cursor()

    # 🔍 Prevent duplicate booking for same ride
    cursor.execute(
        "SELECT * FROM bookings WHERE ride_id=%s",
        (ride_id,)
    )

    if cursor.fetchone():
        cursor.close()
        conn.close()
        return False

    query = """
    INSERT INTO bookings (driver_id, passenger_id, ride_id, fare, status)
    VALUES (%s, %s, %s, %s, 'matched')
    """

    cursor.execute(query, (driver_id, passenger_id, ride_id, fare))

    # 🔥 Update ride status to booked
    cursor.execute(
        "UPDATE rides SET status='booked' WHERE ride_id=%s",
        (ride_id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return True


# ==============================
# 📊 GET BOOKINGS FOR USER
# ==============================
def get_user_bookings(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT b.*, r.start_location, r.destination
    FROM bookings b
    JOIN rides r ON b.ride_id = r.ride_id
    WHERE b.driver_id=%s OR b.passenger_id=%s
    ORDER BY b.booking_id DESC
    """

    cursor.execute(query, (user_id, user_id))
    bookings = cursor.fetchall()

    cursor.close()
    conn.close()

    return bookings


# ==============================
# 🚦 UPDATE BOOKING STATUS
# ==============================
def update_booking_status(booking_id, status):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE bookings SET status=%s WHERE booking_id=%s",
        (status, booking_id)
    )

    conn.commit()
    cursor.close()
    conn.close()


# ==============================
# ⭐ ADD RATING
# ==============================
def add_rating(booking_id, rating):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE bookings SET rating=%s WHERE booking_id=%s",
        (rating, booking_id)
    )

    conn.commit()
    cursor.close()
    conn.close()
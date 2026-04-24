from utils.helpers import get_db_connection

def create_request(user_id, ride_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Prevent duplicate request
    cursor.execute(
        "SELECT * FROM ride_requests WHERE user_id=%s AND ride_id=%s",
        (user_id, ride_id)
    )

    if cursor.fetchone():
        return False

    cursor.execute(
        "INSERT INTO ride_requests (user_id, ride_id) VALUES (%s, %s)",
        (user_id, ride_id)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return True


def get_requests_for_ride(ride_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT rr.*, u.name AS passenger_name
    FROM ride_requests rr
    JOIN users u ON rr.user_id = u.id
    WHERE rr.ride_id=%s
    """

    cursor.execute(query, (ride_id,))
    requests = cursor.fetchall()

    cursor.close()
    conn.close()

    return requests


def update_request_status(request_id, status):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE ride_requests SET status=%s WHERE request_id=%s",
        (status, request_id)
    )

    conn.commit()
    cursor.close()
    conn.close()
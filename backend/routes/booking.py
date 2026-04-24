from flask import Blueprint, jsonify, request
from utils.helpers import token_required
from utils.helpers import get_db_connection

booking_routes = Blueprint('booking', __name__)

@booking_routes.route('/my_bookings', methods=['GET'])
@token_required
def my_bookings():
    user_id = request.user['user_id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM bookings
        WHERE driver_id=%s OR passenger_id=%s
    """, (user_id, user_id))

    bookings = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify(bookings)
@booking_routes.route('/rate', methods=['POST'])
@token_required
def rate():
    data = request.json

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE bookings SET rating=%s WHERE booking_id=%s",
        (data['rating'], data['booking_id'])
    )

    conn.commit()
    cursor.close()
    conn.close()

    return {"message": "Rating submitted"}
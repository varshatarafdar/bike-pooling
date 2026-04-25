from flask import Blueprint, jsonify
from utils.helpers import get_db_connection

admin_routes = Blueprint('admin', __name__)

@admin_routes.route('/admin_stats', methods=['GET'])
def admin_stats():

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # USERS
    cursor.execute("SELECT COUNT(*) as total FROM users")
    users = cursor.fetchone()['total']

    # RIDES
    cursor.execute("SELECT COUNT(*) as total FROM rides")
    rides = cursor.fetchone()['total']

    # MATCHES
    cursor.execute("SELECT COUNT(*) as total FROM bookings WHERE status='matched'")
    matches = cursor.fetchone()['total']

    # REVENUE
    cursor.execute("SELECT SUM(fare) as total FROM bookings")
    revenue = cursor.fetchone()['total'] or 0

    cursor.close()
    conn.close()

    return jsonify({
        "users": users,
        "rides": rides,
        "matches": matches,
        "revenue": revenue
    })
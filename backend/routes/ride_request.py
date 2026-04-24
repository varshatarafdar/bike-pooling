from flask import Blueprint, request, jsonify
from utils.helpers import token_required
from models.ride_request_model import (
    create_request,
    get_requests_for_ride,
    update_request_status
)
from models.booking_model import create_booking

request_routes = Blueprint('request', __name__)


# ==============================
# 📩 SEND RIDE REQUEST (Passenger)
# ==============================
@request_routes.route('/request_ride', methods=['POST'])
@token_required
def request_ride():
    try:
        data = request.json
        user_id = request.user['user_id']

        if "ride_id" not in data:
            return jsonify({"message": "ride_id is required"}), 400

        success = create_request(user_id, data['ride_id'])

        if not success:
            return jsonify({"message": "Request already sent"}), 409

        return jsonify({"message": "Ride request sent 🚀"}), 201

    except Exception as e:
        return jsonify({
            "message": "Failed to send request",
            "error": str(e)
        }), 500


# ==============================
# 📥 GET REQUESTS FOR A RIDE (Driver)
# ==============================
@request_routes.route('/ride_requests/<int:ride_id>', methods=['GET'])
@token_required
def get_requests(ride_id):
    try:
        requests = get_requests_for_ride(ride_id)

        if not requests:
            return jsonify({"message": "No requests found"}), 404

        return jsonify({
            "message": "Requests fetched",
            "requests": requests
        }), 200

    except Exception as e:
        return jsonify({
            "message": "Failed to fetch requests",
            "error": str(e)
        }), 500


# ==============================
# ✅ HANDLE REQUEST (Driver)
# ==============================
@request_routes.route('/handle_request', methods=['POST'])
@token_required
def handle_request():
    try:
        data = request.json

        required_fields = ["request_id", "action", "driver_id", "passenger_id", "ride_id"]
        for field in required_fields:
            if field not in data:
                return jsonify({"message": f"{field} is required"}), 400

        action = data['action'].lower()

        if action not in ["accepted", "rejected"]:
            return jsonify({"message": "Invalid action"}), 400

        # ✅ Update request status
        update_request_status(data['request_id'], action)

        # ✅ If accepted → create booking
        if action == "accepted":
            create_booking(
                data['driver_id'],
                data['passenger_id'],
                data['ride_id'],
                fare=50  # static for now
            )

        return jsonify({
            "message": f"Request {action} successfully"
        }), 200

    except Exception as e:
        return jsonify({
            "message": "Failed to process request",
            "error": str(e)
        }), 500
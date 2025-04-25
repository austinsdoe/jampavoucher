from flask import Blueprint, request, jsonify

# Define the Blueprint
diagnostic_bp = Blueprint("diagnostic", __name__)

# Simple health check endpoint
@diagnostic_bp.route("/api/ping", methods=["GET"])
def ping():
    return jsonify({
        "message": "✅ Flask is reachable!",
        "from_ip": request.remote_addr
    })

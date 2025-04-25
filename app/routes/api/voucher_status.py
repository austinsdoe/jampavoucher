from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.voucher import Voucher
from datetime import datetime
import os

api_bp = Blueprint("api_voucher_status", __name__, url_prefix="/api/voucher")

# Load shared secret for verifying MikroTik API calls
SHARED_SECRET = os.getenv("VOUCHER_API_SECRET", "supersecure123")

@api_bp.route("/status", methods=["POST"])
def update_voucher_status():
    # ✅ Authentication: Require shared token in header
    token = request.headers.get("X-Auth-Token")
    if token != SHARED_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    # ✅ Parse payload
    data = request.get_json()
    code = data.get("code")
    event = data.get("event")  # "start", "expired", "used"
    used_mb = data.get("used_mb")
    ip = data.get("ip")
    mac = data.get("mac")

    if not code or not event:
        return jsonify({"error": "Missing required fields: code or event"}), 400

    # ✅ Fetch voucher
    voucher = Voucher.query.filter_by(code=code.strip().upper()).first()
    if not voucher:
        return jsonify({"error": "Voucher not found"}), 404

    # ✅ Handle event type
    now = datetime.utcnow()

    if event == "start":
        voucher.status = "used"
        voucher.first_used_at = voucher.first_used_at or now
        if ip:
            voucher.used_by_ip = ip
        if mac:
            voucher.used_by_mac = mac

    elif event == "expired":
        voucher.status = "expired"
        voucher.used_at = now

    elif event == "used":
        voucher.status = "used"
        if used_mb is not None:
            voucher.used_mb = float(used_mb)

    # ✅ Track used MB if included
    if used_mb is not None:
        voucher.used_mb = float(used_mb)

    db.session.commit()
    return jsonify({"message": "Voucher status updated successfully"}), 200

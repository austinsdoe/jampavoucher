from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.voucher import Voucher
from datetime import datetime
import os

api_bp = Blueprint("api_voucher_status", __name__, url_prefix="/api/voucher")

# Load shared secret token from environment
SHARED_SECRET = os.getenv("VOUCHER_API_SECRET", "supersecure123")

@api_bp.route("/status", methods=["POST"])
def update_voucher_status():
    # 🔐 Auth via token header
    token = request.headers.get("X-Auth-Token")
    if token != SHARED_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    # 🧾 Parse JSON body
    data = request.get_json() or {}
    code = data.get("code", "").strip().upper()
    event = data.get("event")  # 'start', 'used', 'expired'
    used_mb = data.get("used_mb")
    ip = data.get("ip")
    mac = data.get("mac")

    if not code or not event:
        return jsonify({"error": "Missing required fields: code or event"}), 400

    # 🔍 Find voucher
    voucher = Voucher.query.filter_by(code=code).first()
    if not voucher:
        return jsonify({"error": f"Voucher {code} not found"}), 404

    now = datetime.utcnow()

    # 🧠 Event: First usage
    if event == "start":
        voucher.status = "used"
        voucher.first_used_at = voucher.first_used_at or now
        if ip:
            voucher.used_by_ip = ip
        if mac:
            voucher.used_by_mac = mac

    # 🧠 Event: Periodic usage update
    elif event == "used":
        voucher.status = "used"
        voucher.used_at = now
        if used_mb is not None:
            try:
                mb = float(used_mb)
                if mb > voucher.used_mb:
                    voucher.used_mb = mb
            except Exception:
                pass
        if ip:
            voucher.used_by_ip = ip
        if mac:
            voucher.used_by_mac = mac

    # 🧠 Event: Expired session
    elif event == "expired":
        voucher.status = "expired"
        voucher.used_at = now
        if used_mb is not None:
            try:
                mb = float(used_mb)
                voucher.used_mb = max(voucher.used_mb or 0, mb)
            except Exception:
                pass

    else:
        return jsonify({"error": f"Invalid event type: {event}"}), 400

    # ✅ Final commit
    db.session.commit()

    # Optional: log action
    print(f"[API] Voucher '{code}' updated via event '{event}' at {now}")

    return jsonify({"message": f"Voucher {code} updated successfully."}), 200

from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.voucher import Voucher
from app.models.router import MikroTikRouter
from datetime import datetime
import os
import json

api_bp = Blueprint("api_voucher_status", __name__, url_prefix="/api/voucher")

# Load shared secret token from environment
SHARED_SECRET = os.getenv("VOUCHER_API_SECRET", "supersecure123")


# ✅ Route for POST-based clients (with JSON body)
@api_bp.route("/status", methods=["POST"])
def update_voucher_status():
    token = request.headers.get("X-Auth-Token")
    if token != SHARED_SECRET:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = request.get_json(force=True)
    except Exception:
        try:
            data = json.loads(request.data.decode())
        except Exception:
            return jsonify({"error": "Invalid JSON format"}), 400

    code = data.get("code", "").strip().upper()
    event = data.get("event")
    used_mb = data.get("used_mb")
    ip = data.get("ip")
    mac = data.get("mac")

    if not code or not event:
        return jsonify({"error": "Missing required fields: code or event"}), 400

    voucher = Voucher.query.filter_by(code=code).first()
    if not voucher:
        return jsonify({"error": f"Voucher {code} not found"}), 404

    router = MikroTikRouter.query.filter_by(ip_address=ip).first() if ip else None

    if router and voucher.router_id != router.id:
        return jsonify({"error": "Voucher not valid on this router"}), 403

    now = datetime.utcnow()

    if event == "start":
        voucher.status = "used"
        voucher.first_used_at = voucher.first_used_at or now
        if ip:
            voucher.used_by_ip = ip
        if mac:
            voucher.used_by_mac = mac

    elif event == "used":
        voucher.status = "used"
        voucher.used_at = now
        if used_mb is not None:
            try:
                mb = float(used_mb)
                if mb > (voucher.used_mb or 0):
                    voucher.used_mb = mb
            except Exception:
                pass
        if ip:
            voucher.used_by_ip = ip
        if mac:
            voucher.used_by_mac = mac

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

    if not voucher.used_on_router_id and router:
        voucher.used_on_router_id = router.id

    db.session.commit()
    return jsonify({"message": f"Voucher {code} updated successfully."}), 200


# ✅ MikroTik-compatible GET route
@api_bp.route("/status_get", methods=["GET"])
def update_voucher_status_get():
    code = request.args.get("code", "").strip().upper()
    event = request.args.get("event", "used")
    ip = request.args.get("ip")
    mac = request.args.get("mac")
    used_mb = request.args.get("used_mb")

    if not code or not event:
        return jsonify({"error": "Missing code or event"}), 400

    voucher = Voucher.query.filter_by(code=code).first()
    if not voucher:
        return jsonify({"error": f"Voucher {code} not found"}), 404

    router = MikroTikRouter.query.filter_by(ip_address=ip).first() if ip else None

    if router and voucher.router_id != router.id:
        return jsonify({"error": "Voucher not valid on this router"}), 403

    now = datetime.utcnow()
    voucher.status = event
    voucher.used_at = now
    if ip:
        voucher.used_by_ip = ip
    if mac:
        voucher.used_by_mac = mac

    if used_mb:
        try:
            mb = float(used_mb)
            if mb > (voucher.used_mb or 0):
                voucher.used_mb = mb
        except Exception:
            pass

    if not voucher.used_on_router_id and router:
        voucher.used_on_router_id = router.id

    db.session.commit()
    return jsonify({"message": f"Voucher {code} updated via GET."}), 200


# ✅ Debug test route
@api_bp.route("/test", methods=["POST"])
def test_post():
    return jsonify({"ok": True}), 200

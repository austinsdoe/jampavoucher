from flask import Blueprint, request, jsonify
from app.models.voucher import Voucher
from app.extensions import db
from datetime import datetime
import logging


api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/voucher/status_notify", methods=["GET"])
def voucher_status_notify():
    """
    Called by MikroTik on voucher usage (login).
    Updates voucher as 'inuse', sets first use timestamp, and stores MAC address.
    """
    code = request.args.get("code", "").strip().upper()
    mac = request.args.get("mac", "").strip()

    if not code or not mac:
        return jsonify({"error": "Missing voucher code or MAC"}), 400

    voucher = Voucher.query.filter_by(code=code).first()
    if not voucher:
        return jsonify({"error": "Voucher not found"}), 404

    # Set first use time if not already set
    if not voucher.first_used_at:
        voucher.first_used_at = datetime.utcnow()

    # Update MAC and status
    voucher.used_by_mac = mac
    voucher.status = "inuse"
    db.session.commit()

    return jsonify({
        "message": "Voucher marked as in use",
        "code": voucher.code,
        "status": voucher.status,
        "mac": mac
    })

@api_bp.route("/voucher/status", methods=["POST"])
def voucher_status_post():
    """
    Called by MikroTik script using JSON POST.
    Updates voucher usage event, MAC, and usage info.
    """
    data = request.get_json(force=True)
    app.logger.info(f"[POST /voucher/status] Data received: {data}")

    code = data.get("code", "").strip().upper()
    mac = data.get("mac", "").strip()
    event = data.get("event", "unknown")

    if not code or not mac:
        return jsonify({"error": "Missing code or mac"}), 400

    voucher = Voucher.query.filter_by(code=code).first()
    if not voucher:
        return jsonify({"error": "Voucher not found"}), 404

    if not voucher.first_used_at:
        voucher.first_used_at = datetime.utcnow()

    voucher.used_by_mac = mac
    voucher.status = "used" if event == "used" else "inuse"
    db.session.commit()

    return jsonify({
        "message": "Voucher status updated",
        "code": code,
        "event": event
    })

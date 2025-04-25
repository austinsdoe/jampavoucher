import os
import stripe
from flask import Blueprint, request, jsonify
from datetime import datetime
from app.extensions import db
from app.models.payment import Payment
from app.utils.voucher import create_online_voucher

webhooks_bp = Blueprint("webhooks", __name__, url_prefix="/webhook")

# === Stripe Webhook Setup ===
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")


# ──────────────────────────────────────────────
# 🧠 Shared handler for successful payments
# ──────────────────────────────────────────────
def process_payment_success(tx_id, amount):
    payment = Payment.query.filter_by(transaction_id=tx_id).first()

    if not payment:
        return "Payment not found", 404

    if payment.status == "success":
        return "Already processed", 200

    payment.status = "success"
    payment.paid_at = datetime.utcnow()
    voucher = create_online_voucher(amount)
    payment.voucher = voucher
    db.session.commit()

    print(f"[✔] Payment {tx_id} marked successful, voucher {voucher.code} issued.")
    return "Processed", 200


# ──────────────────────────────────────────────
# 💳 Stripe Webhook
# ──────────────────────────────────────────────
@webhooks_bp.route("/stripe", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except ValueError:
        print("[❌] Invalid Stripe payload")
        return jsonify({"error": "Invalid payload"}), 400
    except stripe.error.SignatureVerificationError:
        print("[❌] Stripe signature verification failed")
        return jsonify({"error": "Invalid signature"}), 400

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        tx_id = metadata.get("tx_id")
        amount = float(session.get("amount_total", 0)) / 100

        if not tx_id:
            return jsonify({"error": "Missing transaction ID"}), 400

        _, status_code = process_payment_success(tx_id, amount)
        return jsonify({"status": "Stripe webhook processed"}), status_code

    return jsonify({"status": "Unhandled Stripe event"}), 200


# ──────────────────────────────────────────────
# 🟧 Orange Money Webhook
# ──────────────────────────────────────────────
@webhooks_bp.route("/orange", methods=["POST"])
def orange_webhook():
    data = request.get_json()
    tx_id = data.get("external_id")
    status = data.get("status")
    amount = float(data.get("amount", 0))

    if not tx_id or not status:
        return jsonify({"error": "Missing tx_id or status"}), 400

    if status == "SUCCESSFUL":
        _, status_code = process_payment_success(tx_id, amount)
    elif status == "FAILED":
        payment = Payment.query.filter_by(transaction_id=tx_id).first()
        if payment and payment.status != "success":
            payment.status = "failed"
            db.session.commit()
        status_code = 200
    else:
        status_code = 400

    return jsonify({"status": "Orange webhook processed"}), status_code


# ──────────────────────────────────────────────
# 🟨 MTN Mobile Money Webhook
# ──────────────────────────────────────────────
@webhooks_bp.route("/mtn", methods=["POST"])
def mtn_webhook():
    data = request.get_json()
    tx_id = data.get("externalId")
    status = data.get("status")
    amount = float(data.get("amount", 0))

    if not tx_id or not status:
        return jsonify({"error": "Missing tx_id or status"}), 400

    if status == "SUCCESSFUL":
        _, status_code = process_payment_success(tx_id, amount)
    elif status == "FAILED":
        payment = Payment.query.filter_by(transaction_id=tx_id).first()
        if payment and payment.status != "success":
            payment.status = "failed"
            db.session.commit()
        status_code = 200
    else:
        status_code = 400

    return jsonify({"status": "MTN webhook processed"}), status_code

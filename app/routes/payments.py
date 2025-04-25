from flask import Blueprint, request, render_template, redirect, url_for, flash
from app.services import PaymentGateway

payments_bp = Blueprint("payments", __name__, url_prefix="/payment")
gateway = PaymentGateway()

# ───────────────────────────────────────────────
# 💳 Payment Landing Page — Choose Payment Method
# ───────────────────────────────────────────────
@payments_bp.route("/", methods=["GET", "POST"])
def pay():
    """
    Landing page for voucher purchase — shows provider options.
    """
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        amount = request.form.get("amount", "").strip()
        provider = request.form.get("provider", "mtn").lower()

        # Validation
        if not phone or not amount:
            flash("⚠️ Phone number and amount are required.", "danger")
            return redirect(url_for("payments.pay"))

        try:
            amount = float(amount)
        except ValueError:
            flash("⚠️ Invalid amount entered.", "danger")
            return redirect(url_for("payments.pay"))

        # Handle provider-specific flow
        if provider == "mtn":
            tx_id = gateway.initiate_mtn_payment(phone, amount)
            return redirect(url_for("payments.status", tx_id=tx_id))
        elif provider == "orange":
            tx_id = gateway.initiate_orange_payment(phone, amount)
            return redirect(url_for("payments.status", tx_id=tx_id))
        elif provider == "stripe":
            return redirect(url_for("payments.stripe_checkout"))
        else:
            flash("⚠️ Unknown payment provider selected.", "danger")

    return render_template("payments/pay.html")

# ────────────────────────────────
# 📞 MTN Mobile Money Payment Flow
# ────────────────────────────────
@payments_bp.route("/mtn", methods=["GET", "POST"])
def mtn_pay():
    if request.method == "POST":
        phone = request.form.get("phone")
        amount = request.form.get("amount", "0")

        try:
            amount = float(amount)
            tx_id = gateway.initiate_mtn_payment(phone, amount)
            return redirect(url_for("payments.status", tx_id=tx_id))
        except Exception as e:
            flash(f"❌ MTN payment error: {str(e)}", "danger")

    return render_template("payments/mtn_pay.html")

# ─────────────────────────────────
# 🟧 Orange Money Payment Flow
# ─────────────────────────────────
@payments_bp.route("/orange", methods=["GET", "POST"])
def orange_pay():
    if request.method == "POST":
        phone = request.form.get("phone")
        amount = request.form.get("amount", "0")

        try:
            amount = float(amount)
            tx_id = gateway.initiate_orange_payment(phone, amount)
            return redirect(url_for("payments.status", tx_id=tx_id))
        except Exception as e:
            flash(f"❌ Orange payment error: {str(e)}", "danger")

    return render_template("payments/orange_pay.html")

# ────────────────────────────────────────
# 💡 Payment Status Check + Voucher Gen
# ────────────────────────────────────────
@payments_bp.route("/status/<tx_id>")
def status(tx_id):
    """
    Check payment status and generate voucher if successful.
    """
    if not tx_id:
        flash("❌ Missing transaction ID.", "danger")
        return redirect(url_for("payments.pay"))

    voucher = gateway.verify_payment_and_create_voucher(tx_id)
    if voucher:
        flash("✅ Payment successful. Voucher generated!", "success")
        return render_template("payments/success.html", voucher=voucher)

    flash("⏳ Payment is still pending or failed.", "warning")
    return render_template("payments/pending.html", tx_id=tx_id)

# ────────────────────────────────
# 💳 Stripe Card Payment Flow
# ────────────────────────────────
@payments_bp.route("/stripe", methods=["GET", "POST"])
def stripe_checkout():
    if request.method == "POST":
        amount = request.form.get("amount", "0")

        try:
            amount = float(amount)
            checkout_url = gateway.create_stripe_checkout_session(amount)
            return redirect(checkout_url)
        except Exception as e:
            flash(f"❌ Stripe error: {str(e)}", "danger")

    return render_template("payments/stripe_pay.html")

# ─────────────────────────────────────
# ✅ Stripe Webhook or Success Redirect
# ─────────────────────────────────────
@payments_bp.route("/stripe-success")
def stripe_success():
    session_id = request.args.get("session_id")
    tx_id = request.args.get("tx_id")

    if not session_id or not tx_id:
        flash("⚠️ Missing Stripe session or transaction ID.", "danger")
        return redirect(url_for("payments.pay"))

    voucher = gateway.handle_stripe_success(session_id, tx_id)
    if voucher:
        flash("✅ Stripe payment successful! Voucher generated.", "success")
        return render_template("payments/success.html", voucher=voucher)

    flash("⚠️ Stripe payment verification failed.", "danger")
    return redirect(url_for("payments.pay"))

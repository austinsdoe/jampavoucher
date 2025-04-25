from flask import Blueprint, render_template, session, redirect, url_for, request, flash
from datetime import datetime, timedelta
from app.models.voucher import Voucher
from app.extensions import db

voucher_user_bp = Blueprint("voucher_user", __name__, url_prefix="/voucher")


@voucher_user_bp.route("/login", methods=["GET", "POST"])
def login_voucher():
    """
    Captive portal login using a voucher code.
    """
    if request.method == "POST":
        code = request.form.get("code", "").strip().upper()
        voucher = Voucher.query.filter_by(code=code).first()

        if not voucher:
            flash("❌ Invalid voucher code.", "danger")
            return redirect(url_for("voucher_user.login_voucher"))

        if voucher.status == "used":
            flash("⚠️ Voucher already in use.", "warning")
            return redirect(url_for("voucher_user.login_voucher"))

        # Activate the voucher on first use
        if not voucher.first_used_at:
            voucher.first_used_at = datetime.utcnow()

        voucher.status = "used"
        session["voucher_code"] = voucher.code
        db.session.commit()

        # ✅ Activate on MikroTik
        if voucher.router:
            try:
                from app.services.mikrotik_api import MikroTikAPI
                api = MikroTikAPI(
                    ip=voucher.router.ip,
                    username=voucher.router.username,
                    password=voucher.router.password,
                    port=voucher.router.api_port
                )
                api.connect()
                # NOTE: Replace this if MAC address is captured via login form
                mac = request.args.get("mac") or request.remote_addr
                api.activate_hotspot_user(username=voucher.code, mac=mac)
            except Exception as e:
                print(f"[❌] Failed to activate voucher on MikroTik: {e}")

        return redirect(url_for("voucher_user.user_dashboard"))

    return render_template("captive/login.html")


@voucher_user_bp.route("/dashboard")
def user_dashboard():
    """
    Displays voucher user dashboard (data/time remaining, etc.).
    """
    code = session.get("voucher_code")
    if not code:
        return redirect(url_for("voucher_user.login_voucher"))

    voucher = Voucher.query.filter_by(code=code).first()
    if not voucher or voucher.status != "used":
        return redirect(url_for("voucher_user.login_voucher"))

    # Time tracking
    start_time = voucher.first_used_at
    expiry_time = start_time + timedelta(days=voucher.plan.duration_days) if start_time else None
    remaining_time = expiry_time - datetime.utcnow() if expiry_time else None

    # Bandwidth tracking
    used_mb = voucher.used_mb or 0
    remaining_mb = max(voucher.plan.bandwidth_limit_mb - used_mb, 0)

    return render_template(
        "voucher/dashboard.html",
        voucher=voucher,
        start_time=start_time,
        expiry_time=expiry_time,
        remaining_mb=remaining_mb,
        remaining_time=remaining_time
    )


@voucher_user_bp.route("/logout")
def logout_voucher():
    """
    Clears voucher session and disconnects from MikroTik.
    """
    code = session.pop("voucher_code", None)

    if code:
        voucher = Voucher.query.filter_by(code=code).first()
        if voucher and voucher.router:
            try:
                from app.services.mikrotik_api import MikroTikAPI
                api = MikroTikAPI(
                    ip=voucher.router.ip,
                    username=voucher.router.username,
                    password=voucher.router.password,
                    port=voucher.router.api_port
                )
                api.connect()
                api.disconnect_user(username=code)
            except Exception as e:
                print(f"[❌] Failed to disconnect user from MikroTik: {e}")

    return redirect(url_for("voucher_user.login_voucher"))

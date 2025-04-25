from flask import Blueprint, render_template, redirect, flash, session
from datetime import timedelta, datetime
from app.extensions import db
from app.models.voucher import Voucher
from app.models.router import MikroTikRouter
from app.services.mikrotik_api import MikroTikAPI

captive_bp = Blueprint("captive", __name__, url_prefix="/voucher")

# 🔌 Disconnect user from MikroTik
def disconnect_user(voucher_code, router):
    try:
        api = MikroTikAPI(ip=router.ip, username=router.username, password=router.password, port=router.api_port)
        api.connect()
        api.disconnect_user(voucher_code)
    except Exception as e:
        print(f"[❌] Failed to disconnect user {voucher_code}: {e}")

# ─────────────────────────────────────────────
# 📊 Voucher Dashboard
# ─────────────────────────────────────────────
@captive_bp.route("/dashboard")
def voucher_user_dashboard():
    code = session.get("voucher_code")
    if not code:
        flash("⚠️ Not logged in with a voucher.", "warning")
        return redirect("/voucher/login")

    voucher = Voucher.query.filter_by(code=code).first()
    if not voucher:
        flash("❌ Invalid session.", "danger")
        return redirect("/voucher/login")

    if voucher.is_expired():
        if voucher.router:
            disconnect_user(voucher.code, voucher.router)
        voucher.status = "expired"
        db.session.commit()
        session.clear()
        flash("⏳ Voucher expired.", "warning")
        return redirect("/voucher/login")

    start_time = voucher.first_used_at
    expiry_time = voucher.expiry_time or (
        voucher.first_used_at + timedelta(days=voucher.validity_days)
        if voucher.first_used_at else None
    )
    remaining_mb = voucher.remaining_mb if hasattr(voucher, 'remaining_mb') else 0

    return render_template("captive/dashboard.html",
        voucher=voucher,
        start_time=start_time,
        expiry_time=expiry_time,
        remaining_mb=remaining_mb
    )

# ─────────────────────────────────────────────
# 🚪 Logout and Cleanup
# ─────────────────────────────────────────────
@captive_bp.route("/logout")
def logout():
    code = session.get("voucher_code")
    if code:
        voucher = Voucher.query.filter_by(code=code).first()
        if voucher and voucher.router:
            disconnect_user(voucher.code, voucher.router)
        session.clear()
        flash("✅ You have been logged out.", "info")
    return redirect("/voucher/login")

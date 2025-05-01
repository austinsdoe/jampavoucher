from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime, timedelta
from app.models.voucher import Voucher
from app.extensions import db

voucher_user_bp = Blueprint("voucher_user", __name__, url_prefix="/voucher")

# 🧭 Dashboard after login
@voucher_user_bp.route("/dashboard")
def user_dashboard():
    from app.models.router import MikroTikRouter
    from app.services.mikrotik_api import MikroTikAPI

    mac = request.args.get("mac")
    code = request.args.get("username")

    if not code or not mac:
        flash("Missing voucher info.", "danger")
        return redirect("http://google.com")

    voucher = Voucher.query.filter_by(code=code).first()
    if not voucher or not voucher.router:
        flash("Voucher not found.", "danger")
        return redirect("http://google.com")

    used_mb = 0
    remaining_mb = 0
    expired = False
    expiry_reason = None
    start_time = voucher.first_used_at
    expiry_time = None

    try:
        api = MikroTikAPI(
            ip=voucher.router.ip_address,
            username=voucher.router.api_username,
            password=voucher.router.api_password,
            port=voucher.router.api_port
        )
        api.connect()

        usage = api.get_voucher_usage(mac)
        if usage:
            used_bytes = usage.get("total-bytes", 0)
            used_mb = used_bytes // (1024 * 1024)
            remaining_mb = max(voucher.plan.bandwidth_limit_mb - used_mb, 0)

            if voucher.plan and used_mb >= voucher.plan.bandwidth_limit_mb:
                expired = True
                expiry_reason = "Data limit reached"

        if voucher.first_used_at:
            expiry_time = voucher.first_used_at + timedelta(days=voucher.plan.duration_days)
            if datetime.utcnow() > expiry_time:
                expired = True
                expiry_reason = "Time expired"

        if expired:
            voucher.status = "expired"
            db.session.commit()
            api.delete_user(code)

    except Exception as e:
        print(f"[❌] Failed to fetch usage or delete expired voucher: {e}")

    return render_template("voucher/dashboard.html", voucher=voucher,
                           used_mb=used_mb,
                           remaining_mb=remaining_mb,
                           expired=expired,
                           expiry_reason=expiry_reason,
                           start_time=start_time,
                           expiry_time=expiry_time)


# 🔓 Logout & disconnect
@voucher_user_bp.route("/logout")
def logout_voucher():
    code = request.args.get("username")
    mac = request.args.get("mac")

    if not code:
        return redirect("http://google.com")

    voucher = Voucher.query.filter_by(code=code).first()
    if voucher and voucher.router:
        try:
            from app.services.mikrotik_api import MikroTikAPI
            api = MikroTikAPI(
                ip=voucher.router.ip_address,
                username=voucher.router.api_username,
                password=voucher.router.api_password,
                port=voucher.router.api_port
            )
            api.connect()
            api.disconnect_user(username=code)
        except Exception as e:
            print(f"[❌] Failed to disconnect user from MikroTik: {e}")

        # ✅ Dynamic redirect to router IP
        redirect_url = f"http://{voucher.router.ip_address}/login"
        return redirect(redirect_url)

    return redirect("http://google.com")


# 📊 API: Get live usage
@voucher_user_bp.route("/usage")
def get_usage():
    code = request.args.get("username")
    mac = request.args.get("mac")

    if not code or not mac:
        return jsonify({"error": "unauthorized"}), 401

    voucher = Voucher.query.filter_by(code=code).first()
    if not voucher or not voucher.router:
        return jsonify({"error": "voucher or router not found"}), 404

    try:
        from app.services.mikrotik_api import MikroTikAPI
        api = MikroTikAPI(
            ip=voucher.router.ip_address,
            username=voucher.router.api_username,
            password=voucher.router.api_password,
            port=voucher.router.api_port
        )
        api.connect()
        usage = api.get_voucher_usage(mac)

        if not usage:
            return jsonify({"error": "no usage found"}), 404

        used_bytes = usage.get("total-bytes", 0)
        used_mb = used_bytes // (1024 * 1024)
        voucher.used_mb = used_mb
        db.session.commit()

        if voucher.plan:
            now = datetime.utcnow()
            expiry_time = voucher.first_used_at + timedelta(days=voucher.plan.duration_days)
            if now > expiry_time or used_mb >= voucher.plan.bandwidth_limit_mb:
                voucher.status = "expired"
                db.session.commit()
                try:
                    api.delete_user(code)
                except Exception as e:
                    print(f"[❌] Auto-delete failed in usage: {e}")

        remaining_mb = max(voucher.plan.bandwidth_limit_mb - used_mb, 0)

        return jsonify({
            "used_mb": used_mb,
            "remaining_mb": remaining_mb,
            "purchased_mb": voucher.plan.bandwidth_limit_mb
        })

    except Exception as e:
        print(f"[❌] Failed to fetch usage: {e}")
        return jsonify({"error": "router error"}), 500


# 🧾 Login GET (shown by MikroTik if you override login.html)
@voucher_user_bp.route("/login", methods=["GET"])
def login_voucher():
    mac = request.args.get("mac")
    ip = request.args.get("ip")
    username = request.args.get("username")
    return render_template("voucher/login.html", mac=mac, ip=ip, username=username)


# 🧾 Login POST (if you implement external login)
@voucher_user_bp.route("/login", methods=["POST"])
def validate_voucher():
    code = request.form.get("code", "").strip().upper()
    mac = request.form.get("mac")
    ip = request.form.get("ip")

    if not code:
        flash("❌ Voucher code is required.", "danger")
        return redirect(url_for("voucher_user.login_voucher", mac=mac, ip=ip, username=""))

    voucher = Voucher.query.filter_by(code=code).first()
    if not voucher:
        flash("❌ Invalid voucher code.", "danger")
        return redirect(url_for("voucher_user.login_voucher", mac=mac, ip=ip, username=""))

    now = datetime.utcnow()
    if not voucher.first_used_at:
        voucher.first_used_at = now
        db.session.commit()

    return redirect(url_for("voucher_user.user_dashboard", mac=mac, username=code))

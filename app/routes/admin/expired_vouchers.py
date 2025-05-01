from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models.voucher import Voucher
from app.models.router import MikroTikRouter
from app.extensions import db

# ✅ Correct blueprint name for use as 'admin.expired_admin'
expired_bp = Blueprint("expired_admin", __name__, url_prefix="/expired")

@expired_bp.route("/expired-vouchers")
def expired_vouchers():
    router_id = request.args.get("router_id", type=int)
    query = Voucher.query.filter_by(status="expired")

    if router_id:
        query = query.filter_by(router_id=router_id)

    vouchers = query.order_by(Voucher.first_used_at.desc()).all()
    routers = MikroTikRouter.query.all()

    return render_template("admin/expired_vouchers.html", vouchers=vouchers, routers=routers)

@expired_bp.route("/expired-vouchers/delete", methods=["POST"])
def delete_expired():
    codes = request.form.getlist("voucher_codes")
    if not codes:
        flash("⚠️ No vouchers selected.", "warning")
        return redirect(url_for("admin.expired_admin.expired_vouchers"))

    deleted = []
    for code in codes:
        voucher = Voucher.query.filter_by(code=code).first()
        if voucher:
            try:
                db.session.delete(voucher)
                deleted.append(code)
            except Exception as e:
                print(f"[❌] Failed to delete voucher {code}: {e}")

    db.session.commit()
    flash(f"✅ Deleted {len(deleted)} expired voucher(s) from database.", "success")
    return redirect(url_for("admin.expired_admin.expired_vouchers"))

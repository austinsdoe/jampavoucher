from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models.voucher import Voucher
from app.models.router import MikroTikRouter
from app.extensions import db
from app.decorators import role_required

# 🧭 Blueprint mounted under /vouchers
vouchers_by_router_bp = Blueprint("vouchers_by_router", __name__, url_prefix="/vouchers")


# 📄 View all vouchers filtered by router
@vouchers_by_router_bp.route("/")
@login_required
@role_required("admin")
def all_vouchers():
    router_id = request.args.get("router_id", type=int)
    query = Voucher.query

    if router_id:
        query = query.filter_by(router_id=router_id)

    vouchers = query.order_by(Voucher.created_at.desc()).all()
    routers = MikroTikRouter.query.order_by(MikroTikRouter.name.asc()).all()

    return render_template("admin/vouchers_by_router.html",
        vouchers=vouchers,
        routers=routers,
        selected_router_id=router_id)


# 🗑️ Delete selected vouchers
@vouchers_by_router_bp.route("/delete", methods=["POST"])
@login_required
@role_required("admin")
def delete_selected_vouchers():
    codes = request.form.getlist("voucher_codes")
    if not codes:
        flash("⚠️ No vouchers selected for deletion.", "warning")
        return redirect(url_for("vouchers_by_router.all_vouchers"))

    deleted = 0
    for code in codes:
        voucher = Voucher.query.filter_by(code=code).first()
        if voucher:
            try:
                db.session.delete(voucher)
                deleted += 1
            except Exception as e:
                print(f"[❌] Failed to delete voucher {code}: {e}")

    db.session.commit()
    flash(f"✅ Deleted {deleted} voucher(s).", "success")
    return redirect(url_for("vouchers_by_router.all_vouchers"))

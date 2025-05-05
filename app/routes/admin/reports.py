from flask import Blueprint, render_template, request, send_file, flash
from flask_login import login_required
from sqlalchemy import func
from datetime import datetime
import pandas as pd
import os

from app.utils.roles import role_required
from app.models import Voucher, Payment, User, MikroTikRouter
from app.extensions import db

reports_bp = Blueprint("admin_reports", __name__, url_prefix="/admin/reports")

# 📈 Sales Report (unchanged)
@reports_bp.route("/sales")
@login_required
@role_required("admin")
def sales_report():
    start = request.args.get("start")
    end = request.args.get("end")
    query = Payment.query
    if start:
        query = query.filter(Payment.timestamp >= start)
    if end:
        query = query.filter(Payment.timestamp <= end)
    sales = query.order_by(Payment.timestamp.desc()).all()
    return render_template("reports/sales.html", sales=sales, start=start, end=end)

# 📊 Usage Report (router-enforced, export-ready)
@reports_bp.route("/usage")
@login_required
@role_required("admin")
def usage_report():
    start = request.args.get("start")
    end = request.args.get("end")
    router_id = request.args.get("router", type=int)
    export = request.args.get("export")

    query = Voucher.query.filter(Voucher.status == "used")
    if start:
        query = query.filter(Voucher.first_used_at >= start)
    if end:
        query = query.filter(Voucher.first_used_at <= end)
    if router_id:
        query = query.filter(Voucher.router_id == router_id)

    vouchers = query.order_by(Voucher.first_used_at.desc()).all()
    routers = MikroTikRouter.query.order_by(MikroTikRouter.name.asc()).all()

    if export == "csv":
        try:
            df = pd.DataFrame([{
                "Code": v.code,
                "Plan": v.plan_name or (v.plan.name if v.plan else ""),
                "Router": v.router.name if v.router else "N/A",
                "IP": v.used_by_ip or "",
                "MAC": v.used_by_mac or "",
                "Used MB": v.used_mb or 0,
                "First Used": v.first_used_at.strftime("%Y-%m-%d %H:%M") if v.first_used_at else "",
                "Last Update": v.used_at.strftime("%Y-%m-%d %H:%M") if v.used_at else ""
            } for v in vouchers])

            path = os.path.join("exports", f"usage_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv")
            os.makedirs("exports", exist_ok=True)
            df.to_csv(path, index=False)
            return send_file(path, as_attachment=True)
        except Exception as e:
            flash(f"Export failed: {e}", "danger")

    # (PDF export can be added similarly)

    return render_template("reports/usage_report.html",
        vouchers=vouchers,
        routers=routers,
        start=start,
        end=end,
        selected_router=router_id)

# 👤 Staff Performance Report (unchanged)
@reports_bp.route("/staff")
@login_required
@role_required("admin")
def staff_report():
    start = request.args.get("start")
    end = request.args.get("end")

    query = Voucher.query
    if start:
        query = query.filter(Voucher.created_at >= start)
    if end:
        query = query.filter(Voucher.created_at <= end)

    stats = query.with_entities(
        Voucher.created_by_id,
        func.count(Voucher.id).label("total_vouchers"),
        func.sum(Voucher.price).label("total_sales")
    ).group_by(Voucher.created_by_id).all()

    staff = {u.id: u.username for u in User.query.filter_by(role="staff").all()}

    return render_template("reports/staff_report.html",
        stats=stats,
        staff=staff,
        start=start,
        end=end)

from flask import Blueprint, render_template, flash
from flask_login import login_required
from datetime import datetime, timedelta
from sqlalchemy import func
from app.models import MikroTikRouter, Voucher, Payment, User
from app.decorators import role_required

# ✅ Route prefix is /admin/dashboard
dashboard_bp = Blueprint("dashboard", __name__, url_prefix='/dashboard')  # Mounted under /admin in __init__.py

@dashboard_bp.route("/")
@login_required
@role_required("admin")
def dashboard():
    """
    Admin dashboard view showing summary stats and 7-day charts.
    """
    today = datetime.utcnow().date()
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    labels = [d.strftime("%b %d") for d in last_7_days]

    sales_by_day = {d: 0 for d in last_7_days}
    usage_by_day = {d: 0 for d in last_7_days}

    # 🧾 Aggregate payments
    try:
        sales = (
            Payment.query.with_entities(func.date(Payment.timestamp), func.sum(Payment.amount))
            .filter(Payment.timestamp >= last_7_days[0])
            .group_by(func.date(Payment.timestamp))
            .all()
        )
        for date, amount in sales:
            if date in sales_by_day:
                sales_by_day[date] = float(amount)
    except Exception as e:
        flash(f"⚠️ Failed to aggregate sales: {e}", "warning")

    # 🎟️ Aggregate voucher usage
    try:
        usage = (
            Voucher.query.with_entities(func.date(Voucher.first_used_at), func.count(Voucher.id))
            .filter(Voucher.first_used_at >= last_7_days[0])
            .group_by(func.date(Voucher.first_used_at))
            .all()
        )
        for date, count in usage:
            if date in usage_by_day:
                usage_by_day[date] = int(count)
    except Exception as e:
        flash(f"⚠️ Failed to aggregate voucher usage: {e}", "warning")

    # 🧮 Totals
    total_routers = MikroTikRouter.query.count()
    total_vouchers = Voucher.query.count()
    total_staff = User.query.filter_by(role="staff").count()
    total_hotspot = MikroTikRouter.query.filter_by(hotspot_enabled=True).count()
    voucher = Voucher.query.order_by(Voucher.created_at.desc()).first()

    flash("✅ Admin dashboard loaded", "info")

    return render_template("admin/dashboard.html",
        total_routers=total_routers,
        total_vouchers=total_vouchers,
        total_staff=total_staff,
        total_hotspot_servers=total_hotspot,
        routers=MikroTikRouter.query.order_by(MikroTikRouter.name.asc()).all(),
        chart_labels=labels,
        chart_sales=[sales_by_day[d] for d in last_7_days],
        chart_usage=[usage_by_day[d] for d in last_7_days],
        voucher=voucher
    )

from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func
from datetime import datetime, timedelta

from app.extensions import db
from app.models.voucher import Voucher
from app.models.payment import Payment
from app.models.router import MikroTikRouter
from app.models.voucher_batch import VoucherBatch

analytics_bp = Blueprint("analytics", __name__, url_prefix="/dashboard")


@analytics_bp.route("/")
@login_required
def analytics_dashboard():
    """Main admin dashboard displaying analytics and KPIs."""
    today = datetime.utcnow().date()
    start_of_week = today - timedelta(days=6)

    # ─────────────────────────────────────────────
    # 📊 Voucher Status Counts
    # ─────────────────────────────────────────────
    total_vouchers = db.session.query(func.count(Voucher.id)).scalar()
    used = db.session.query(func.count(Voucher.id)).filter_by(status='used').scalar()
    unused = db.session.query(func.count(Voucher.id)).filter_by(status='unused').scalar()
    expired = db.session.query(func.count(Voucher.id)).filter_by(status='expired').scalar()

    # ─────────────────────────────────────────────
    # 💰 Revenue by Payment Provider (successful only)
    # ─────────────────────────────────────────────
    revenue_by_provider = dict(
        db.session.query(
            Payment.provider,
            func.coalesce(func.sum(Payment.amount), 0)
        )
        .filter(Payment.status == "success")
        .group_by(Payment.provider)
        .all()
    )

    # ─────────────────────────────────────────────
    # 🖨️ Total Printed Vouchers (via batches)
    # ─────────────────────────────────────────────
    printed_batches = db.session.query(
        func.coalesce(func.sum(VoucherBatch.quantity), 0)
    ).filter_by(printed=True).scalar() or 0

    # ─────────────────────────────────────────────
    # 🚀 Top 5 Routers by Voucher Usage
    # ─────────────────────────────────────────────
    top_routers = db.session.query(
        MikroTikRouter.name,
        func.count(Voucher.id)
    ).join(Voucher, MikroTikRouter.id == Voucher.router_id)\
     .group_by(MikroTikRouter.name)\
     .order_by(func.count(Voucher.id).desc())\
     .limit(5).all()

    # ─────────────────────────────────────────────
    # 📅 Weekly Voucher Creation Trend (last 7 days)
    # ─────────────────────────────────────────────
    daily_counts = []
    for i in range(7):
        day = start_of_week + timedelta(days=i)
        day_start = datetime.combine(day, datetime.min.time())
        day_end = datetime.combine(day, datetime.max.time())

        count = Voucher.query.filter(
            Voucher.created_at >= day_start,
            Voucher.created_at <= day_end
        ).count()
        daily_counts.append((day.strftime('%a'), count))

    return render_template("admin/dashboard.html",  # ✅ Fixed path
                           total_vouchers=total_vouchers,
                           used=used,
                           unused=unused,
                           expired=expired,
                           printed_vouchers=printed_batches,
                           revenue_by_provider=revenue_by_provider,
                           top_routers=top_routers,
                           daily_counts=daily_counts)

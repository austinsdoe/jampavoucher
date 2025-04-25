from flask import Blueprint, render_template
from flask_login import login_required
from app.decorators import role_required
from app.models import IPChangeLog, MikroTikRouter

ip_logs_bp = Blueprint("ip_logs", __name__, url_prefix="/admin/ip_logs")

@ip_logs_bp.route("/")
@login_required
@role_required("admin")
def view_ip_logs():
    logs = (
        IPChangeLog.query.order_by(IPChangeLog.changed_at.desc())
        .join(MikroTikRouter, MikroTikRouter.id == IPChangeLog.router_id)
        .add_columns(
            IPChangeLog.old_ip,
            IPChangeLog.new_ip,
            IPChangeLog.changed_at,
            MikroTikRouter.name.label("router_name")
        )
        .limit(100)
        .all()
    )
    return render_template("admin/ip_logs.html", logs=logs)

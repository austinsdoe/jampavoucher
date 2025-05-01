from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required
from app.models.router import MikroTikRouter
from app.services.mikrotik_api import MikroTikAPI
from app.decorators import role_required

active_users_bp = Blueprint("active_users", __name__, url_prefix="/admin/active-users")

@active_users_bp.route("/")
@login_required
@role_required("admin")
def list_active_users():
    router_id = request.args.get("router_id", type=int)
    if not router_id:
        flash("Router ID is required.", "danger")
        return redirect(url_for("admin.dashboard"))

    router = MikroTikRouter.query.get(router_id)
    if not router:
        flash("Router not found.", "danger")
        return redirect(url_for("admin.dashboard"))

    try:
        api = MikroTikAPI(
            ip=router.ip_address,
            username=router.api_username,
            password=router.api_password,
            port=router.api_port
        )
        api.connect()
        active_users = api.get_active_users()

    except Exception as e:
        flash(f"Failed to fetch active users: {e}", "danger")
        active_users = []

    return render_template("admin/active_users.html", router=router, active_users=active_users)

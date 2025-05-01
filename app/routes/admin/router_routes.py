from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required
from app.models import db, MikroTikRouter, Voucher, VoucherBatch
from app.forms.router_form import RouterForm
from app.decorators import role_required
from app.services.mikrotik_api import MikroTikAPI
from app.utils.network import ping_router
from app.utils.security import decrypt
from ipaddress import IPv4Network

router_bp = Blueprint("routers", __name__, url_prefix="/routers")

# 🌐 List All Routers
@router_bp.route("/")
@login_required
@role_required("admin")
def manage_routers():
    routers = MikroTikRouter.query.order_by(MikroTikRouter.created_at.desc()).all()
    return render_template("admin/routers.html", routers=routers, ping_router=ping_router)

# ➕ Add or Edit Router
@router_bp.route("/new", methods=["GET", "POST"])
@router_bp.route("/<int:router_id>/edit", methods=["GET", "POST"])
@login_required
@role_required("admin")
def router_form(router_id=None):
    router = MikroTikRouter.query.get(router_id) if router_id else None
    form = RouterForm(obj=router)

    if form.validate_on_submit():
        if not router:
            router = MikroTikRouter()
        form.populate_obj(router)
        db.session.add(router)
        db.session.commit()
        flash("🌐 Router saved successfully.", "success")
        return redirect(url_for("admin.routers.manage_routers"))

    return render_template("admin/router_form.html", form=form, router=router)

# 🗑️ Delete Router (with safety check)
@router_bp.route("/<int:router_id>/delete", methods=["POST", "GET"])
@login_required
@role_required("admin")
def delete_router(router_id):
    linked_batches = VoucherBatch.query.filter_by(router_id=router_id).count()
    if linked_batches > 0:
        flash(f"❌ Cannot delete router: {linked_batches} linked voucher batches exist.", "danger")
        return redirect(url_for("admin.routers.manage_routers"))

    router = MikroTikRouter.query.get_or_404(router_id)
    db.session.delete(router)
    db.session.commit()
    flash("🗑️ Router deleted successfully.", "info")
    return redirect(url_for("admin.routers.manage_routers"))

# 📊 Router Analytics
@router_bp.route("/<int:router_id>/analytics")
@login_required
@role_required("admin")
def router_analytics(router_id):
    router = MikroTikRouter.query.get_or_404(router_id)
    total = Voucher.query.filter_by(router_id=router.id).count()
    used = Voucher.query.filter_by(router_id=router.id, status="used").count()
    expired = Voucher.query.filter_by(router_id=router.id, status="expired").count()
    batches = VoucherBatch.query.filter_by(router_id=router.id).order_by(VoucherBatch.created_at.desc()).all()
    return render_template("admin/router_analytics.html", router=router, total=total, used=used, expired=expired, batches=batches)

# 📡 Ping Router API
@router_bp.route("/<int:router_id>/ping", methods=["GET", "POST"])
@login_required
@role_required("admin")
def ping_router_view(router_id):
    router = MikroTikRouter.query.get_or_404(router_id)
    result = None

    if request.method == "POST":
        try:
            api = MikroTikAPI(
                ip=router.ip_address,
                username=router.api_username,
                password=decrypt(router._api_password),
                port=router.api_port
            )
            is_online = api.ping()
            result = "✅ Router is Online" if is_online else "❌ Router is Offline"
        except Exception as e:
            result = f"⚠️ Error pinging router: {e}"

    return render_template("admin/ping_router.html", router=router, result=result)

# ⚙️ Configure Router
@router_bp.route("/configure/<int:router_id>", methods=["GET", "POST"])
@login_required
@role_required("admin")
def configure_router(router_id):
    router = MikroTikRouter.query.get_or_404(router_id)
    api = MikroTikAPI(
        ip=router.ip_address,
        username=router.api_username,
        password=decrypt(router._api_password),
        port=router.api_port
    )

    if not api.connect(router):
        flash("❌ Could not connect to router.", "danger")
        return redirect(url_for("admin.routers.manage_routers"))

    if request.method == "POST":
        interface = request.form.get("interface")
        ip_address = request.form.get("ip_address")
        dns_servers = request.form.get("dns_servers")
        profile_name = request.form.get("profile_name")
        rate_limit = request.form.get("rate_limit")
        queue_limit = request.form.get("queue_limit")

        try:
            if interface and ip_address:
                api.assign_ip_to_interface(interface, ip_address)
            if dns_servers:
                dns_list = [x.strip() for x in dns_servers.split(",")]
                api.set_dns_servers(dns_list)
            if profile_name:
                api.create_user_profile(profile_name, rate_limit=rate_limit)
            if ip_address and queue_limit:
                api.create_simple_queue(f"queue_{router.name}", ip_address, queue_limit)

            flash("✅ Router configured successfully.", "success")
        except Exception as e:
            flash(f"❌ Configuration failed: {str(e)}", "danger")

    return render_template("admin/router_config.html", router=router)

# ✅ Router API Status (used in dashboard JS)
@router_bp.route("/check-api-status/<int:router_id>")
@login_required
@role_required("admin")
def check_api_status(router_id):
    router = MikroTikRouter.query.get_or_404(router_id)
    try:
        api = MikroTikAPI(
            ip=router.ip_address,
            username=router.api_username,
            password=decrypt(router._api_password),
            port=router.api_port
        )
        status = "online" if api.connect(router) else "offline"
    except Exception:
        status = "offline"
    return jsonify({"status": status})

# 🛠 Configure IP (CIDR + AJAX Interfaces)
@router_bp.route("/configure-ip", methods=["GET", "POST"])
@login_required
@role_required("admin")
def configure_ip():
    routers = MikroTikRouter.query.all()
    if request.method == "POST":
        router_id = request.form.get("router_id")
        interface = request.form.get("interface")
        cidr_input = request.form.get("cidr_address")

        if not cidr_input or "/" not in cidr_input:
            flash("❌ Invalid CIDR format. Example: 192.168.88.1/24", "danger")
            return redirect(url_for("admin.routers.configure_ip"))

        try:
            ip_address, netmask_bits = cidr_input.split("/")
            netmask = str(IPv4Network(f"0.0.0.0/{netmask_bits}", strict=False).netmask)
        except Exception:
            flash("❌ Invalid CIDR format. Example: 192.168.88.1/24", "danger")
            return redirect(url_for("admin.routers.configure_ip"))

        router = MikroTikRouter.query.get(router_id)
        if not router:
            flash("Router not found", "danger")
            return redirect(url_for("admin.routers.configure_ip"))

        api = MikroTikAPI(
            ip=router.ip_address,
            username=router.api_username,
            password=decrypt(router._api_password),
            port=router.api_port,
        )

        if not api.connect(router):
            flash("Failed to connect to MikroTik router.", "danger")
            return redirect(url_for("admin.routers.configure_ip"))

        try:
            api.assign_ip_to_interface(interface, ip_address, netmask)
            flash(f"✅ Assigned {ip_address} to {interface} on {router.name}", "success")
        except Exception as e:
            flash(f"❌ Failed to assign IP: {str(e)}", "danger")

        return redirect(url_for("admin.routers.configure_ip"))

    return render_template("admin/configure_ip.html", routers=routers)

# 🔌 API: Get interface list (AJAX)
@router_bp.route("/api/<int:router_id>/interfaces")
@login_required
@role_required("admin")
def get_router_interfaces(router_id):
    router = MikroTikRouter.query.get_or_404(router_id)
    api = MikroTikAPI(
        ip=router.ip_address,
        username=router.api_username,
        password=decrypt(router._api_password),
        port=router.api_port,
    )

    if not api.connect(router):
        return jsonify({"status": "error", "message": "Could not connect"}), 500

    try:
        interfaces = api.api.get_resource("/interface/ethernet").get()
        ip_resources = api.api.get_resource("/ip/address").get()

        ip_map = {}
        for ip_entry in ip_resources:
            iface = ip_entry.get("interface")
            ip = ip_entry.get("address")
            if iface:
                ip_map.setdefault(iface, []).append(ip)

        for iface in interfaces:
            iface["ip_addresses"] = ip_map.get(iface.get("name"), [])

        return jsonify({"status": "ok", "interfaces": interfaces})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 🌐 List interfaces across routers
@router_bp.route("/interfaces")
@login_required
@role_required("admin")
def list_interfaces():
    routers = MikroTikRouter.query.all()
    router_interfaces = []

    for router in routers:
        api = MikroTikAPI(
            ip=router.ip_address,
            username=router.api_username,
            password=decrypt(router._api_password),
            port=router.api_port,
        )
        if api.connect(router):
            try:
                interfaces = api.api.get_resource("/interface/ethernet").get()
                ip_resources = api.api.get_resource("/ip/address").get()

                ip_map = {}
                for ip_entry in ip_resources:
                    iface = ip_entry.get("interface")
                    ip = ip_entry.get("address")
                    if iface:
                        ip_map.setdefault(iface, []).append(ip)

                for iface in interfaces:
                    iface["ip_addresses"] = ip_map.get(iface.get("name"), [])

                router_interfaces.append({
                    "router": router,
                    "interfaces": interfaces
                })
            except Exception as e:
                router_interfaces.append({
                    "router": router,
                    "interfaces": [],
                    "error": str(e)
                })
        else:
            router_interfaces.append({
                "router": router,
                "interfaces": [],
                "error": "❌ Could not connect"
            })

    return render_template("admin/interfaces_list.html", router_interfaces=router_interfaces)

# 🛰️ Manually Trigger MikroTik Script: notifyVoucherStatus
@router_bp.route("/<int:router_id>/run-notify-script")
@login_required
@role_required("admin")
def run_notify_script(router_id):
    router = MikroTikRouter.query.get_or_404(router_id)
    try:
        api = MikroTikAPI(
            ip=router.ip_address,
            username=router.api_username,
            password=decrypt(router._api_password),
            port=router.api_port,
        )
        if api.connect():
            api.run_script("notifyVoucherStatus")
            flash(f"✅ Script 'notifyVoucherStatus' executed on {router.name}", "success")
        else:
            flash("❌ Could not connect to MikroTik API.", "danger")
    except Exception as e:
        flash(f"❌ Error executing script: {str(e)}", "danger")
    return redirect(url_for("routers.manage_routers"))

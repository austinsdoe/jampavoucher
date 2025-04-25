from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models import MikroTikRouter, IPChangeLog
from app.services.mikrotik_api import MikroTikAPI
import os

mikrotik_api_bp = Blueprint('mikrotik_api', __name__)

@mikrotik_api_bp.route('/api/update_ip', methods=['GET'])
def update_router_ip():
    token = request.args.get('token')
    new_ip = request.args.get('ip')
    router_id = request.args.get('router_id')  # dynamically passed

    # ✅ Step 1: Validate token
    if token != os.getenv("ROUTER_UPDATE_TOKEN"):
        return jsonify({"error": "Unauthorized"}), 403

    # ✅ Step 2: Validate required parameters
    if not new_ip:
        return jsonify({"error": "Missing 'ip' parameter"}), 400
    if not router_id:
        return jsonify({"error": "Missing 'router_id' parameter"}), 400

    # ✅ Step 3: Fetch the router by ID
    router = MikroTikRouter.query.filter_by(id=router_id).first()
    if not router:
        return jsonify({"error": "Router not found"}), 404

    # ✅ Step 4: Update router IP
    old_ip, updated_ip = MikroTikAPI.update_router_ip(router, new_ip)

    # ✅ Step 5: Log the change only if IP has changed
    if old_ip != updated_ip:
        log = IPChangeLog(
            router_id=router.id,
            old_ip=old_ip,
            new_ip=updated_ip
        )
        db.session.add(log)
        db.session.commit()

    return jsonify({
        "message": "✅ IP updated successfully",
        "router_name": router.name,
        "old_ip": old_ip,
        "new_ip": updated_ip
    }), 200


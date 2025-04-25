from flask import Blueprint

# 🧭 Composite Admin Blueprint mounted at /admin
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Modular admin routes
from .dashboard_routes import dashboard_bp
from .plan_routes import plan_bp
from .router_routes import router_bp
from .staff_routes import staff_bp as admin_staff_bp
from .voucher_routes import voucher_bp as admin_voucher_bp
from .reports import reports_bp as admin_reports_bp
from app.routes.admin.ip_logs import ip_logs_bp

# Register all sub-blueprints
admin_bp.register_blueprint(dashboard_bp)
admin_bp.register_blueprint(plan_bp)
admin_bp.register_blueprint(router_bp)
admin_bp.register_blueprint(admin_staff_bp)
admin_bp.register_blueprint(admin_voucher_bp)
admin_bp.register_blueprint(admin_reports_bp)
admin_bp.register_blueprint(ip_logs_bp)

from flask import Blueprint

# 🧭 Composite Admin Blueprint mounted at /admin
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# ─────────────────────────────────────────────
# Modular admin route blueprints
# ─────────────────────────────────────────────
from .dashboard_routes import dashboard_bp
from .plan_routes import plan_bp
from .router_routes import router_bp
from .staff_routes import staff_bp as admin_staff_bp
from .voucher_routes import voucher_bp as admin_voucher_bp
from .reports import reports_bp as admin_reports_bp
from .ip_logs import ip_logs_bp
from .expired_vouchers import expired_bp as expired_admin_bp
from app.routes.vouchers_by_router import vouchers_by_router_bp
from app.routes.admin.active_users import active_users_bp         # ✅ NEW

# ─────────────────────────────────────────────
# Register all admin sub-blueprints
# ─────────────────────────────────────────────
admin_bp.register_blueprint(dashboard_bp)
admin_bp.register_blueprint(plan_bp)
admin_bp.register_blueprint(router_bp)
admin_bp.register_blueprint(admin_staff_bp)
admin_bp.register_blueprint(admin_voucher_bp)
admin_bp.register_blueprint(admin_reports_bp)
admin_bp.register_blueprint(ip_logs_bp)
admin_bp.register_blueprint(expired_admin_bp, name="expired_admin")            # ✅ Named namespace
admin_bp.register_blueprint(vouchers_by_router_bp, name="vouchers_by_router")  # ✅ Named namespace
admin_bp.register_blueprint(active_users_bp, name="active_users")              # ✅ New Active Users module

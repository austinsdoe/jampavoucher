from flask import Flask

# Models (optional for CLI or shell context)
from app.models.user import User
from app.models.router import MikroTikRouter
from app.models.voucher import Voucher
from app.models.voucher_batch import VoucherBatch
from app.models.user_usage import UserUsage
from app.models.payment import Payment
from app.models.plan import Plan

# Blueprints
from app.routes.admin import admin_bp
from app.routes.auth import auth_bp
from app.routes.analytics import analytics_bp
from app.routes.reports import reports_bp
from app.routes.webhooks import webhooks_bp
from app.routes.voucher_user import voucher_user_bp
from app.routes.captive_portal import captive_bp
from app.routes.payments import payments_bp
from app.routes.vouchers import vouchers_bp
from app.routes.mikrotik_api import mikrotik_api_bp
from app.routes.diagnostic import diagnostic_bp

# ✅ CORRECTED IMPORT for /api/voucher/status
from app.routes.api.voucher_status import api_bp
from app.routes.api.test_ping import ping_test

def register_routes(app: Flask):
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(webhooks_bp)
    app.register_blueprint(voucher_user_bp)
    app.register_blueprint(captive_bp)
    app.register_blueprint(payments_bp)
    app.register_blueprint(vouchers_bp)
    app.register_blueprint(mikrotik_api_bp)
    app.register_blueprint(diagnostic_bp)
    app.register_blueprint(api_bp)        # ✅ /api/voucher/status is now correctly registered
    app.register_blueprint(ping_test)

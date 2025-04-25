from .register import register_routes
from app.routes.api.voucher_status import api_bp

def register_all_routes(app):
    app.register_blueprint(api_bp)
    register_routes(app)

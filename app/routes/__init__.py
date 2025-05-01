from .register import register_routes
from app.routes.api import api_bp  # ✅ corrected flat-file import

def register_all_routes(app):
    app.register_blueprint(api_bp)
    register_routes(app)

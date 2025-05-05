from .register import register_routes
from app.routes.api_routes import api_bp  # ✅ Corrected flat-file import

def register_all_routes(app):
    app.register_blueprint(api_bp)
    register_routes(app)

import os
from datetime import timedelta
from flask import Flask, redirect
from dotenv import load_dotenv
from flask_babel import Babel

# 🔄 Load environment variables (safe absolute path loading)
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path)

# 🔧 Core Extensions
from app.extensions import db, login_manager, limiter, migrate
from app.models.user import User
from app.models.router import MikroTikRouter  # Needed for router listing
from app.utils.network import ping_router     # ✅ Used to detect online routers

# 🌍 Localization
babel = Babel()

# 🧭 Modular Admin Blueprint registration
from app.routes.register import register_routes as register_admin_routes

# 🧹 CLI Tasks
from app.cli.cleanup import cleanup_expired
from app.cli.router_cli import sync_routers_command


def create_app():
    app = Flask(__name__)

    # 📦 Load configuration
    config_path = os.getenv("APP_CONFIG", "config.dev.DevConfig").strip()
    app.config.from_object(config_path)
    app.config['BABEL_DEFAULT_LOCALE'] = 'en'
    app.permanent_session_lifetime = timedelta(hours=4)

    # 🌍 Initialize localization
    babel.init_app(app)

    # 🔌 Initialize core extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    limiter.init_app(app)

    # 🔐 Setup Login Manager
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."

    # 🧭 Register all route blueprints
    register_admin_routes(app)

    # ⤴️ Root redirect
    @app.route('/')
    def root_redirect():
        return redirect('/dashboard')

 

    # 📁 Ensure /data directory exists
    app_root = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(app_root, "..", ".."))
    data_dir = os.path.join(project_root, "data")
    os.makedirs(data_dir, exist_ok=True)
    app.config['DATA_DIR'] = data_dir

    # 📦 Inject online routers for navbar dropdown
    @app.context_processor
    def inject_routers():
        try:
            routers = MikroTikRouter.query.order_by(MikroTikRouter.name.asc()).all()
            online_routers = [r for r in routers if ping_router(r.ip)]
        except Exception:
            online_routers = []
        return dict(online_routers=online_routers)

    # 🧹 Register CLI commands
    app.cli.add_command(cleanup_expired)
    app.cli.add_command(sync_routers_command)

    return app

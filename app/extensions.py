import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from cryptography.fernet import Fernet

# ──────────────────────────────
# 📦 Core Flask Extensions
# ──────────────────────────────

db = SQLAlchemy()

migrate = Migrate()  # 🔄 For database migrations

login_manager = LoginManager()
login_manager.login_view = 'auth.login'  # 🔐 Redirect path for unauthenticated users

limiter = Limiter(key_func=get_remote_address)

# ──────────────────────────────
# 🔐 Fernet Encryption Setup
# ──────────────────────────────

FERNET_SECRET_KEY = os.getenv("FERNET_SECRET_KEY")

if not FERNET_SECRET_KEY:
    raise RuntimeError("❌ Missing FERNET_SECRET_KEY in environment variables (.env).")

try:
    fernet = Fernet(FERNET_SECRET_KEY.encode())
except Exception as e:
    raise ValueError(f"❌ Invalid FERNET_SECRET_KEY: must be 32 url-safe base64-encoded bytes.\nDetails: {e}")

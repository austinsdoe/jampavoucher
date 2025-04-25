import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from app.extensions import db
from app.models.user import User
from werkzeug.security import generate_password_hash

# ────────────────
# Setup
# ────────────────
app = create_app()

with app.app_context():
    username = input("Enter admin username: ").strip().lower()
    password = input("Enter admin password: ").strip()

    existing = User.query.filter_by(username=username).first()
    if existing:
        print("❌ User already exists.")
    else:
        user = User(username=username, password_hash=generate_password_hash(password), role="admin")
        db.session.add(user)
        db.session.commit()
        print("✅ Admin user created successfully.")


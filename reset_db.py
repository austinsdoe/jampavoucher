# reset_db.py

import os
from app import create_app
from app.extensions import db

# Prevent running in production or staging
env = os.getenv("FLASK_ENV", "development")
if env not in ["development", "testing"]:
    raise RuntimeError(f"❌ Cannot run reset_db.py in '{env}' environment!")

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()
    print("✅ Database reset successfully.")

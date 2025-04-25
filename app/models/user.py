from app.extensions import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Role constants
USER_ROLES = ("admin", "staff", "voucher_user")

class User(db.Model, UserMixin):
    """System user (admin, staff, or voucher_user)."""
    __tablename__ = "user"
    __table_args__ = {'extend_existing': True}  # 👈 ADD THIS LINE

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(db.String(20), default="staff")

    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"

    def __str__(self):
        return self.username

    # 🔐 Password methods
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    # 🔐 Role check helpers
    def is_admin(self):
        return self.role == "admin"

    def is_staff(self):
        return self.role == "staff"

    def is_voucher_user(self):
        return self.role == "voucher_user"

from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.ext.hybrid import hybrid_property
from app.extensions import db
from app.encryption import encrypt_value, decrypt_value

# ──────────────────────────────────────────────────────────────
# Constants for roles, statuses, and providers (maintainability)
# ──────────────────────────────────────────────────────────────
USER_ROLES = ('admin', 'staff')
VOUCHER_STATUSES = ('unused', 'used', 'expired', 'printed')
PAYMENT_STATUSES = ('pending', 'success', 'failed')
PAYMENT_PROVIDERS = ('mtn', 'orange', 'stripe')


# ──────────────────────────────────────────────────────────────
# User Model
# ──────────────────────────────────────────────────────────────
class User(db.Model, UserMixin):
    """Admin or Staff user."""
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(512), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ──────────────────────────────────────────────────────────────
# MikroTik Router
# ──────────────────────────────────────────────────────────────
class MikroTikRouter(db.Model):
    """Represents a managed MikroTik router."""
    __tablename__ = 'mikro_tik_router'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    host = db.Column(db.String(100), nullable=False)
    port = db.Column(db.Integer, default=8728)
    username_encrypted = db.Column(db.String(256), nullable=False)
    password_encrypted = db.Column(db.String(512), nullable=False)
    mac_address = db.Column(db.String(64))
    location = db.Column(db.String(255))
    is_public = db.Column(db.Boolean, default=False)
    active = db.Column(db.Boolean, default=True)
    last_connected_at = db.Column(db.DateTime)

    added_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    added_by_user = db.relationship('User', backref='routers_added')

    def __repr__(self):
        return f"<Router {self.name} ({self.host})>"

    @hybrid_property
    def username(self):
        return decrypt_value(self.username_encrypted)

    @username.setter
    def username(self, value):
        self.username_encrypted = encrypt_value(value)

    @hybrid_property
    def password(self):
        return decrypt_value(self.password_encrypted)

    @password.setter
    def password(self, value):
        self.password_encrypted = encrypt_value(value)


# ──────────────────────────────────────────────────────────────
# Voucher Batch
# ──────────────────────────────────────────────────────────────
class VoucherBatch(db.Model):
    """Batch of vouchers generated at once."""
    __tablename__ = 'voucher_batch'

    id = db.Column(db.Integer, primary_key=True)
    router_id = db.Column(db.Integer, db.ForeignKey('mikro_tik_router.id'))
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    plan_name = db.Column(db.String(50))
    quantity = db.Column(db.Integer, default=500)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    printed = db.Column(db.Boolean, default=False)

    vouchers = db.relationship('Voucher', backref='batch', lazy=True)


# ──────────────────────────────────────────────────────────────
# Voucher
# ──────────────────────────────────────────────────────────────
class Voucher(db.Model):
    """Individual voucher with plan and usage info."""
    __tablename__ = 'voucher'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False)
    type = db.Column(db.String(20), default='offline')  # offline / online
    plan_name = db.Column(db.String(50), nullable=False)
    bandwidth_limit_mb = db.Column(db.Integer, nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)

    status = db.Column(db.String(20), default='unused')
    first_used_at = db.Column(db.DateTime)
    valid_until = db.Column(db.DateTime)

    router_id = db.Column(db.Integer, db.ForeignKey('mikro_tik_router.id'))
    used_on_router_id = db.Column(db.Integer, db.ForeignKey('mikro_tik_router.id'))
    batch_id = db.Column(db.Integer, db.ForeignKey('voucher_batch.id'))
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    used_at = db.Column(db.DateTime)
    used_by_ip = db.Column(db.String(50))

    def __repr__(self):
        return f"<Voucher {self.code} ({self.plan_name})>"

    def is_used(self):
        return self.status in ('used', 'expired')

    def mark_used(self):
        self.status = 'used'
        self.used_at = datetime.utcnow()


# ──────────────────────────────────────────────────────────────
# User Usage
# ──────────────────────────────────────────────────────────────
class UserUsage(db.Model):
    """Tracks per-session usage of a voucher."""
    __tablename__ = 'user_usage'

    id = db.Column(db.Integer, primary_key=True)
    voucher_code = db.Column(db.String(50), db.ForeignKey('voucher.code'))
    router_id = db.Column(db.Integer, db.ForeignKey('mikro_tik_router.id'))
    mac_address = db.Column(db.String(50))
    ip_address = db.Column(db.String(50))
    session_start = db.Column(db.DateTime)
    session_end = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Integer)
    data_used_mb = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ──────────────────────────────────────────────────────────────
# Payment
# ──────────────────────────────────────────────────────────────
class Payment(db.Model):
    """Logs payments from MTN, Orange, or Stripe."""
    __tablename__ = 'payment'

    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(50), nullable=False)  # mtn, orange, stripe
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, success, failed
    transaction_id = db.Column(db.String(100), unique=True)
    voucher_id = db.Column(db.Integer, db.ForeignKey('voucher.id'))
    router_id = db.Column(db.Integer, db.ForeignKey('mikro_tik_router.id'))
    paid_by = db.Column(db.String(100))
    user_phone = db.Column(db.String(20))
    paid_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

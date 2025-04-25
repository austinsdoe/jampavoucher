from datetime import datetime, timedelta
from app.extensions import db
from app.models.router import MikroTikRouter
from app.services.mikrotik_api import MikroTikAPI

class Voucher(db.Model):
    __tablename__ = 'voucher'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)

    plan_id = db.Column(db.Integer, db.ForeignKey('plan.id'), nullable=False)
    plan_name = db.Column(db.String(128), nullable=True)
    data_cap = db.Column(db.Integer, nullable=True)  # In MB
    price = db.Column(db.Float, nullable=True)

    status = db.Column(db.String(20), default='unused', index=True)
    first_used_at = db.Column(db.DateTime, nullable=True)
    valid_until = db.Column(db.DateTime, nullable=True)
    used_at = db.Column(db.DateTime, nullable=True)

    used_by_ip = db.Column(db.String(50), nullable=True)
    used_by_mac = db.Column(db.String(50), nullable=True)
    used_mb = db.Column(db.Float, default=0.0, nullable=False)

    type = db.Column(db.String(20), default='offline')

    router_id = db.Column(db.Integer, db.ForeignKey('mikro_tik_router.id'), nullable=True)
    used_on_router_id = db.Column(db.Integer, db.ForeignKey('mikro_tik_router.id'), nullable=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('voucher_batch.id'), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ──────────────── Relationships ────────────────
    plan = db.relationship('Plan', backref='vouchers')
    router = db.relationship('MikroTikRouter', foreign_keys=[router_id], backref='vouchers_for_batch')
    used_on_router = db.relationship('MikroTikRouter', foreign_keys=[used_on_router_id], backref='vouchers_used')
    creator = db.relationship('User', backref='created_vouchers', lazy=True)

    # ──────────────── Core Logic ────────────────
    def __repr__(self):
        return f"<Voucher {self.code} - Plan: {self.plan.name if self.plan else self.plan_name} - Status: {self.status}>"

    def __str__(self):
        return f"Voucher {self.code} ({self.plan.name if self.plan else self.plan_name})"

    def mark_first_use(self):
        """Marks voucher as used and sets expiry based on plan duration."""
        if not self.first_used_at:
            now = datetime.utcnow()
            self.first_used_at = now
            duration_days = getattr(self.plan, 'duration_days', 0) if self.plan else 0
            self.valid_until = now + timedelta(days=duration_days)
            self.used_at = now
            self.status = 'used'
            db.session.commit()

    def add_usage(self, mb_used):
        """Adds used MB to local tracker."""
        if not isinstance(mb_used, (int, float)) or mb_used < 0:
            raise ValueError("Usage must be a positive number")
        self.used_mb += mb_used
        db.session.commit()

    def is_expired(self):
        """True if expired by time or cap (with optional MikroTik check)."""
        now = datetime.utcnow()
        time_expired = self.valid_until is not None and now > self.valid_until

        # Real-time data check
        try:
            if self.used_by_mac and self.router_id:
                router = MikroTikRouter.query.get(self.router_id)
                if router:
                    api = MikroTikAPI(router.ip, router.username, router.password, router.api_port)
                    api.connect()
                    usage = api.get_voucher_usage(self.used_by_mac)
                    if usage and self.data_cap:
                        used_mb = usage["total-bytes"] / (1024 * 1024)
                        return time_expired or (used_mb >= self.data_cap)
        except Exception as e:
            print(f"[⚠️] Voucher expiry usage check failed: {e}")

        # Fallback local check
        cap = self.data_cap or (self.plan.bandwidth_limit_mb if self.plan else 0)
        local_data_expired = cap > 0 and self.used_mb >= cap

        return time_expired or local_data_expired

    def expire(self):
        """Force expire a voucher."""
        if self.status != 'expired':
            self.status = 'expired'
            db.session.commit()

    # ──────────────── Properties ────────────────
    @property
    def percent_used(self):
        """Percentage of data consumed (from local tracker)."""
        cap = self.data_cap or (self.plan.bandwidth_limit_mb if self.plan else 0)
        return round((self.used_mb / cap) * 100, 2) if cap else 0

    @property
    def remaining_mb(self):
        """Real-time remaining MB (fallbacks to data_cap - used_mb)."""
        try:
            if self.used_by_mac and self.router_id:
                router = MikroTikRouter.query.get(self.router_id)
                if router:
                    api = MikroTikAPI(router.ip, router.username, router.password, router.api_port)
                    api.connect()
                    usage = api.get_voucher_usage(self.used_by_mac)
                    if usage and self.data_cap:
                        used = usage["total-bytes"] / (1024 * 1024)
                        return max(self.data_cap - used, 0)
        except Exception as e:
            print(f"[⚠️] Remaining MB check failed: {e}")
        return max((self.data_cap or 0) - self.used_mb, 0)

    @property
    def is_used(self):
        return self.status == 'used'

    @property
    def is_unused(self):
        return self.status == 'unused'

    @property
    def display_status(self):
        if self.status == "unused":
            return "Not Used"
        elif self.status == "used":
            return f"Used on {self.used_at.strftime('%Y-%m-%d')}" if self.used_at else "Used"
        elif self.status == "expired":
            return "Expired"
        return self.status

    # ──────────────── Alias ────────────────
    @property
    def expires_at(self):
        """Alias for valid_until"""
        return self.valid_until

    @expires_at.setter
    def expires_at(self, value):
        self.valid_until = value

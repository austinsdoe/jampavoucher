from datetime import datetime
from app.extensions import db


class VoucherBatch(db.Model):
    __tablename__ = 'voucher_batch'

    # ────── Core Fields ──────
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=True)  # Optional label for batch

    router_id = db.Column(db.Integer, db.ForeignKey('mikro_tik_router.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('plan.id'), nullable=False)

    quantity = db.Column(db.Integer, nullable=False, default=500)
    printed = db.Column(db.Boolean, default=False)
    exported_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ────── Upload Tracking ──────
    upload_status = db.Column(db.String(20), default="pending")  # "pending", "uploaded"
    upload_date = db.Column(db.DateTime, nullable=True)

    # ────── Relationships ──────
    creator = db.relationship('User', backref='created_voucher_batches')
    plan = db.relationship('Plan', backref='voucher_batches')
    router = db.relationship('MikroTikRouter', backref='voucher_batches')
    vouchers = db.relationship(
        'Voucher',
        backref='batch',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    # ────── Representations ──────
    def __repr__(self):
        return f"<VoucherBatch #{self.id} - Plan: {self.plan.name if self.plan else 'N/A'} - Qty: {self.quantity}>"

    def __str__(self):
        return f"Batch {self.id} ({self.plan.name if self.plan else 'N/A'})"

    # ────── Utilities ──────
    def mark_exported(self, commit: bool = True):
        """Mark this batch as exported (printed) with a timestamp."""
        self.printed = True
        self.exported_at = datetime.utcnow()
        if commit:
            db.session.commit()

    def mark_uploaded(self, commit: bool = True):
        """Mark this batch as uploaded to a router."""
        self.upload_status = "uploaded"
        self.upload_date = datetime.utcnow()
        if commit:
            db.session.commit()

    def count_by_status(self, status: str) -> int:
        """Return the count of vouchers with a given status."""
        return self.vouchers.filter_by(status=status).count()

    # ────── Computed Properties ──────
    @property
    def used_count(self) -> int:
        return self.count_by_status("used")

    @property
    def unused_count(self) -> int:
        return self.count_by_status("unused")

    @property
    def expired_count(self) -> int:
        return self.count_by_status("expired")

    @property
    def usage_ratio(self) -> float:
        """Return percentage of vouchers used from the batch."""
        if not self.quantity:
            return 0.0
        return round((self.used_count / self.quantity) * 100, 2)

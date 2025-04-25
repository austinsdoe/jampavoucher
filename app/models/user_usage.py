from datetime import datetime
from app.extensions import db


class UserUsage(db.Model):
    """
    Tracks a voucher session used by a device (IP + MAC) on a router.
    """
    __tablename__ = 'user_usage'

    id = db.Column(db.Integer, primary_key=True)

    # Voucher reference
    voucher_code = db.Column(
        db.String(50), db.ForeignKey('voucher.code'), nullable=False
    )

    # Router context
    router_id = db.Column(db.Integer, db.ForeignKey('mikro_tik_router.id'), nullable=True)
    mac_address = db.Column(db.String(50))
    ip_address = db.Column(db.String(50))

    # Session tracking
    session_start = db.Column(db.DateTime, default=db.func.now())
    session_end = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Integer)
    data_used_mb = db.Column(db.Float)

    # Timestamp
    created_at = db.Column(db.DateTime, default=db.func.now())
    timed_out = db.Column(db.Boolean, default=False)

    # Relationships
    router = db.relationship('MikroTikRouter', backref='usage_logs')
    voucher = db.relationship('Voucher', backref='usage_logs')

    def end_session(self, data_used_mb=None):
        """
        Marks the session as ended and calculates duration.
        """
        if not self.session_end:
            self.session_end = datetime.utcnow()
            self.duration_minutes = int(
                (self.session_end - self.session_start).total_seconds() / 60
            )
            if data_used_mb is not None:
                self.data_used_mb = round(data_used_mb, 2)

    def __repr__(self):
        return f"<UserUsage {self.voucher_code} on {self.router.name if self.router else 'Unknown Router'}>"

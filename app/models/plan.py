from datetime import datetime
from app.extensions import db



class Plan(db.Model):
    __tablename__ = 'plan'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    bandwidth_limit_mb = db.Column(db.Integer, nullable=False)
    duration_days = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False, default=0.00)
    description = db.Column(db.Text, nullable=True)
    rate_limit = db.Column(db.String(50), nullable=True)
    mikrotik_profile = db.Column(db.String(50), nullable=True)  # ✅ new field
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ────── Representation ──────
    def __repr__(self) -> str:
        bw = f"{self.bandwidth_limit_mb}MB" if self.bandwidth_limit_mb else "Unlimited"
        days = f"{self.duration_days}d" if self.duration_days else "No Expiry"
        return f"<Plan {self.name} - {bw} for {days}>"

    def as_dict(self) -> dict:
        """Returns the plan as a dictionary — useful for API or admin UI."""
        return {
            "id": self.id,
            "name": self.name,
            "bandwidth_limit_mb": self.bandwidth_limit_mb,
            "duration_days": self.duration_days,
            "price": self.price,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

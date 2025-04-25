from app.extensions import db
from datetime import datetime

class Payment(db.Model):
    """Represents a mobile money or card payment made for a voucher."""
    __tablename__ = "payment"

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(100), unique=True, nullable=False)
    provider = db.Column(db.String(20), nullable=False)  # mtn, orange, stripe, paypal
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default="LRD")
    phone_number = db.Column(db.String(30), nullable=True)

    status = db.Column(db.String(20), default="pending")  # pending, success, failed

    paid_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 🔗 Voucher association
    voucher_id = db.Column(db.Integer, db.ForeignKey("voucher.id"), nullable=True)
    voucher = db.relationship("Voucher", backref="payment")

    # 🔗 Staff (user) association — fix FK tablename to "user"
    staff_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    staff = db.relationship("User", backref="payments")
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


    def __repr__(self):
        return f"<Payment {self.transaction_id} | {self.provider} | {self.amount} {self.currency}>"

from app.extensions import db
from datetime import datetime

class IPChangeLog(db.Model):
    __tablename__ = "ip_change_logs"

    id = db.Column(db.Integer, primary_key=True)
    
    # ✅ Corrected FK to match MikroTikRouter's __tablename__
    router_id = db.Column(db.Integer, db.ForeignKey("mikro_tik_router.id"), nullable=False)
    
    old_ip = db.Column(db.String(100))
    new_ip = db.Column(db.String(100))
    changed_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<IPChangeLog router_id={self.router_id} old={self.old_ip} new={self.new_ip}>"

from app.extensions import db, fernet

class MikroTikRouter(db.Model):
    __tablename__ = 'mikro_tik_router'  # must match the referenced FK in other models

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(50), nullable=False)
    api_username = db.Column(db.String(50), nullable=False)
    _api_password = db.Column("api_password", db.LargeBinary, nullable=False)
    location = db.Column(db.String(100))

    api_port = db.Column(db.Integer, default=8728)

    created_at = db.Column(db.DateTime, server_default=db.func.now())
    hotspot_enabled = db.Column(db.Boolean, default=False)
    routeros_version = db.Column(db.String(32), nullable=True)
    login_mode = db.Column(db.String(16), nullable=True)

    # ✅ Optional: relationship to access IP change logs from router
    ip_logs = db.relationship("IPChangeLog", backref="router", lazy=True)

    def __repr__(self):
        return f"<Router {self.name} - {self.ip_address}>"

    @property
    def api_password(self):
        try:
            return fernet.decrypt(self._api_password).decode()
        except Exception:
            return ""

    @api_password.setter
    def api_password(self, value):
        if value:
            self._api_password = fernet.encrypt(value.encode())

    def mask_password(self):
        return '*' * 8 if self._api_password else ''

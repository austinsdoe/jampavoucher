from config.base import BaseConfig

class ProdConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    
    CAPTIVE_PORTAL_BASE_URL = os.getenv("CAPTIVE_PORTAL_BASE_URL", "http://http://127.0.0.1:5000//voucher/login")


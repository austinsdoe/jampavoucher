# config/dev.py
import os
from config.base import BaseConfig

class DevConfig(BaseConfig):
    # Flask core settings
    DEBUG = True
    TESTING = False
    SESSION_COOKIE_SECURE = False

    # Secret and Encryption keys
    SECRET_KEY = os.getenv("SECRET_KEY", "your_very_secret_key")
    FERNET_SECRET_KEY = os.getenv("FERNET_SECRET_KEY", "fxD7I7Vfm_Jk4JwoOHzIFmcBVulNiBPNelif9AXFdO4=")
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "fxD7I7Vfm_Jk4JwoOHzIFmcBVulNiBPNelif9AXFdO4=")

    # Database settings
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://austin:Schollbo11@localhost:5432/mikrotikdb")
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Stripe configuration
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "sk_live_xxx")
    STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY", "pk_live_xxx")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_xxx")

    # Orange Money configuration
    ORANGE_CLIENT_ID = os.getenv("ORANGE_CLIENT_ID", "your_orange_client_id")
    ORANGE_CLIENT_SECRET = os.getenv("ORANGE_CLIENT_SECRET", "your_orange_client_secret")

    # MTN Mobile Money configuration
    MTN_SUBSCRIPTION_KEY = os.getenv("MTN_SUBSCRIPTION_KEY", "your_mtn_subscription_key")
    MTN_TOKEN = os.getenv("MTN_TOKEN", "your_mtn_access_token")
    MTN_ENVIRONMENT = os.getenv("MTN_ENVIRONMENT", "sandbox")

    # Application base URL
    BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")
    CAPTIVE_PORTAL_BASE_URL = os.getenv("CAPTIVE_PORTAL_BASE_URL", "http://http://127.0.0.1:5000//voucher/login")


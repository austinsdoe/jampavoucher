# config/prod.py
import os
from config.base import BaseConfig

class ProdConfig(BaseConfig):
    # Flask core settings
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True  # Only send cookies over HTTPS in production

# Secret and Encryption keys (use secure values in .env during real use)
    SECRET_KEY = os.getenv("SECRET_KEY", "dbfedb6de6cf8a85e8c0bfcf4b1939f361df661190914fed89123228a00c4930")
    FERNET_SECRET_KEY = os.getenv("FERNET_SECRET_KEY", "WnoYsXdwAfmnrTFCfV5a_BR0OSqoBIK4jJ1uvaJlVto=")
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "t9Wv4B7tbAuHnrC7Fl6lURSHzxZunPah-TESvdZY5no=")

    # Database settings
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://jampa:Schollbo11@localhost:5432/jampavoucher"
    )
    
    SQLALCHEMY_ECHO = False  # Do not log SQL statements
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Stripe configuration
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "sk_live_your_production_key")
    STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY", "pk_live_your_production_key")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "whsec_your_production_webhook_secret")

    # Orange Money configuration
    ORANGE_CLIENT_ID = os.getenv("ORANGE_CLIENT_ID", "your_production_orange_client_id")
    ORANGE_CLIENT_SECRET = os.getenv("ORANGE_CLIENT_SECRET", "your_production_orange_client_secret")

    # MTN Mobile Money configuration
    MTN_SUBSCRIPTION_KEY = os.getenv("MTN_SUBSCRIPTION_KEY", "your_production_mtn_subscription_key")
    MTN_TOKEN = os.getenv("MTN_TOKEN", "your_production_mtn_access_token")
    MTN_ENVIRONMENT = os.getenv("MTN_ENVIRONMENT", "production")  # should be 'production' not 'sandbox' in live environment

    # Application URLs
    BASE_URL = os.getenv("BASE_URL", "https://http://138.68.75.109/")  # Set your production domain here
    CAPTIVE_PORTAL_BASE_URL = os.getenv("CAPTIVE_PORTAL_BASE_URL", "https://http://138.68.75.109//voucher/login")

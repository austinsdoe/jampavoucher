import os

class BaseConfig:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///voucher.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes in seconds
    RATELIMIT_HEADERS_ENABLED = True

    # Stripe & Encryption
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLIC_KEY = os.getenv("STRIPE_PUBLIC_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    FERNET_SECRET_KEY = os.getenv("FERNET_SECRET_KEY", "")
    BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")

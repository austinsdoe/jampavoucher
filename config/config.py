import os


class Config:
    # Flask core
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')  # Always override in production!

    CAPTIVE_PORTAL_BASE_URL = os.getenv("CAPTIVE_PORTAL_BASE_URL", "http://http://127.0.0.1:5000//voucher/login")

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'postgresql://austin:Schollbo11@localhost:5432/mikrotikdb')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS

    # Rate Limiting
    RATELIMIT_HEADERS_ENABLED = True

    # Stripe & Encryption (Optional defaults for dev)
    STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY', '')
    STRIPE_PUBLIC_KEY = os.getenv('STRIPE_PUBLIC_KEY', '')
    FERNET_SECRET_KEY = os.getenv('FERNET_SECRET_KEY', '')

    # App Base URL
    BASE_URL = os.getenv('BASE_URL', 'http://localhost:5000')
    
    CAPTIVE_PORTAL_HOST = os.getenv("CAPTIVE_PORTAL_HOST", "voucher.portal.local")


import os

class ProdConfig:
    SECRET_KEY = os.environ.get("SECRET_KEY", "6db7fa6e05218ee246a9803e2237542d04dee5d1960f6a6e60d599db730a9e65")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "postgresql://austin:passSchollbo11@localhost/mikrotikdb")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False
    SESSION_COOKIE_SECURE = True
# app/routes/api/test_ping.py
from flask import Blueprint

ping_test = Blueprint("ping_test", __name__)

@ping_test.route("/ping")
def ping():
    print("✅ MikroTik reached /ping endpoint")
    return "pong"

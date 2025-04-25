import os
import qrcode
from flask import current_app

QR_FOLDER = "static/qr"

def generate_qr(code):
    if not os.path.exists(QR_FOLDER):
        os.makedirs(QR_FOLDER)

    base_url = current_app.config.get("CAPTIVE_PORTAL_BASE_URL", "http://localhost/voucher/login")
    url = f"{base_url}?code={code}"

    img = qrcode.make(url)
    path = os.path.join(QR_FOLDER, f"{code}.png")
    img.save(path)
    return path

from cryptography.fernet import Fernet
from flask import current_app

# Load secret key from Flask app config
def get_fernet():
    key = current_app.config.get("FERNET_SECRET_KEY")
    if not key:
        raise ValueError("Missing FERNET_SECRET_KEY in config.")
    return Fernet(key.encode())

def decrypt(cipher_text):
    fernet = get_fernet()
    if isinstance(cipher_text, bytes):
        decrypted_bytes = fernet.decrypt(cipher_text)
    else:
        decrypted_bytes = fernet.decrypt(cipher_text.encode())
    return decrypted_bytes.decode()

def encrypt(plain_text):
    fernet = get_fernet()
    return fernet.encrypt(plain_text.encode())

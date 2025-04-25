# app/encryption.py
from cryptography.fernet import Fernet
from app.extensions import fernet

def encrypt_value(value: str) -> str:
    return fernet.encrypt(value.encode()).decode()

def decrypt_value(token: str) -> str:
    return fernet.decrypt(token.encode()).decode()

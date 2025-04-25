# /app/utils/network.py
import socket

def ping_router(ip):
    try:
        with socket.create_connection((ip, 8728), timeout=1):
            return True
    except Exception:
        return False

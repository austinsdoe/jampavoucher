import socket

def ping_router(ip, port=8728, timeout=1):
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except Exception:
        return False

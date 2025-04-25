from functools import wraps
from flask import abort, request
from flask_login import current_user


def role_required(*roles):
    """
    Flask decorator to restrict access to users with specific roles.
    Usage:
        @role_required("admin")
        def dashboard(): ...
        
        @role_required("admin", "staff")
        def view(): ...
    """
    def wrapper(func):
        @wraps(func)
        def decorated_view(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(403)

            if current_user.role not in roles:
                # Optional: Log denied access attempt (e.g. for audit)
                print(f"[ACCESS DENIED] Role '{current_user.role}' attempted to access {request.path}")
                abort(403)

            return func(*args, **kwargs)
        return decorated_view
    return wrapper

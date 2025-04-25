from functools import wraps
from flask import redirect, url_for, flash
from flask_login import current_user

def role_required(*roles):
    """
    Decorator to restrict access to users with one of the specified roles.
    Usage:
        @role_required("admin")
        @role_required("admin", "staff")
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            if not current_user.is_authenticated:
                flash("You must be logged in to access this page.", "warning")
                return redirect(url_for("auth.login"))

            if current_user.role not in roles:
                flash("Access denied. You do not have permission to access this page.", "danger")
                return redirect(url_for("main.dashboard") if hasattr(current_user, 'role') else "/")

            return view_func(*args, **kwargs)
        return wrapped_view
    return decorator

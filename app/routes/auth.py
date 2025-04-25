from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, limiter
from app.forms.staff_form import StaffForm
from app.models.user import User

# ✅ Register with standard name "auth" so url_for("auth.login") works
auth_bp = Blueprint("auth", __name__)

# ──────────────────────────────────────────────
# 🔐 LOGIN ROUTE (Rate Limited)
# ──────────────────────────────────────────────
@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    """Authenticates users (admin, staff, voucher_user)."""
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            session.permanent = True
            flash("✅ Welcome back!", "success")

            # Redirect based on role
            if user.role in ("admin", "staff"):
                return redirect(url_for("admin.dashboard.dashboard"))
            return redirect(url_for("voucher_user.user_dashboard"))

        flash("❌ Invalid username or password.", "danger")

    return render_template("login.html")


# ──────────────────────────────────────────────
# 🚪 LOGOUT ROUTE
# ──────────────────────────────────────────────
@auth_bp.route("/logout")
@login_required
def logout():
    """Logs out the current user and redirects to the start page."""
    logout_user()
    session.clear()
    flash("👋 You’ve been logged out.", "info")
    return redirect("/")


# ──────────────────────────────────────────────
# 🔒 ADMIN-ONLY CHECK
# ──────────────────────────────────────────────
def admin_only_redirect():
    """Ensures the current user is an admin, else redirects."""
    if not current_user.is_authenticated or current_user.role != "admin":
        flash("⛔ Unauthorized access.", "danger")
        return redirect(url_for("admin.dashboard.dashboard"))
    return None


# ──────────────────────────────────────────────
# 👥 LIST STAFF ACCOUNTS
# ──────────────────────────────────────────────
@auth_bp.route("/staff")
@login_required
def list_staff():
    if (redirect_resp := admin_only_redirect()):
        return redirect_resp

    staff = User.query.filter(User.role != "voucher_user").order_by(User.username.asc()).all()
    return render_template("admin/staff_list.html", staff=staff)


# ──────────────────────────────────────────────
# ➕ CREATE STAFF ACCOUNT
# ──────────────────────────────────────────────
@auth_bp.route("/staff/new", methods=["GET", "POST"])
@login_required
def create_staff():
    if (redirect_resp := admin_only_redirect()):
        return redirect_resp

    form = StaffForm()
    if form.validate_on_submit():
        new_user = User(
            username=form.username.data.strip().lower(),
            password_hash=generate_password_hash(form.password.data),
            role=form.role.data
        )
        db.session.add(new_user)
        db.session.commit()
        flash("✅ Staff account created.", "success")
        return redirect(url_for("auth.list_staff"))

    return render_template("admin/staff_form.html", form=form)


# ──────────────────────────────────────────────
# ✏️ EDIT STAFF ACCOUNT
# ──────────────────────────────────────────────
@auth_bp.route("/staff/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def edit_staff(user_id):
    if (redirect_resp := admin_only_redirect()):
        return redirect_resp

    user = User.query.get_or_404(user_id)
    form = StaffForm(obj=user)

    if form.validate_on_submit():
        user.username = form.username.data.strip().lower()
        user.role = form.role.data
        if form.password.data:
            user.password_hash = generate_password_hash(form.password.data)
        db.session.commit()
        flash("✅ Staff account updated.", "success")
        return redirect(url_for("auth.list_staff"))

    return render_template("admin/staff_form.html", form=form)

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from app.decorators import role_required
from app.forms.staff_form import StaffForm
from app.models import db, User

staff_bp = Blueprint("admin_staff", __name__, url_prefix="/admin/staff")


@staff_bp.route("/")
@login_required
@role_required("admin")
def staff_accounts():
    """List all staff users."""
    form = StaffForm()  # ✅ Provide form to staff_accounts page
    staff = User.query.filter_by(role="staff").order_by(User.username.asc()).all()
    return render_template("admin/staff_accounts.html", staff=staff, form=form)


@staff_bp.route("/create", methods=["GET", "POST"])
@login_required
@role_required("admin")
def create_staff():
    """Create a new staff account."""
    form = StaffForm()
    if form.validate_on_submit():
        if _is_duplicate_username(form.username.data):
            flash("⚠️ Username already exists.", "danger")
            return render_template("admin/staff_form.html", form=form)

        user = User(username=form.username.data, role=form.role.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash("✅ Staff account created successfully!", "success")
        return redirect(url_for("admin.admin_staff.staff_accounts"))  # ✅ corrected endpoint

    return render_template("admin/staff_form.html", form=form)


@staff_bp.route("/edit/<int:user_id>", methods=["GET", "POST"])
@login_required
@role_required("admin")
def edit_staff(user_id):
    """Edit staff username, role, and/or password."""
    user = User.query.get_or_404(user_id)
    form = StaffForm(obj=user)
    form.username.data = user.username  # Prefill

    if form.validate_on_submit():
        if user.username != form.username.data and _is_duplicate_username(form.username.data):
            flash("⚠️ Username already exists.", "danger")
            return render_template("admin/staff_form.html", form=form, is_edit=True)

        user.username = form.username.data
        user.role = form.role.data
        if form.password.data:
            user.set_password(form.password.data)

        db.session.commit()
        flash("✅ Staff account updated successfully!", "success")
        return redirect(url_for("admin.admin_staff.staff_accounts"))  # ✅ corrected

    return render_template("admin/staff_form.html", form=form, is_edit=True)


@staff_bp.route("/delete/<int:user_id>", methods=["POST"])
@login_required
@role_required("admin")
def delete_staff(user_id):
    """Delete a staff account."""
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("🗑️ Staff account deleted.", "info")
    return redirect(url_for("admin.admin_staff.staff_accounts"))  # ✅ corrected


# 🔁 Helper
def _is_duplicate_username(username):
    return User.query.filter_by(username=username).first() is not None

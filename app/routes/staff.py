from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.utils.roles import role_required
from app.models.voucher_batch import VoucherBatch

staff_bp = Blueprint("staff", __name__, url_prefix="/staff")


@staff_bp.route("/dashboard")
@login_required
@role_required("staff")
def dashboard():
    """
    Staff-only dashboard showing their own voucher batches.
    """
    my_batches = VoucherBatch.query \
        .filter_by(created_by_id=current_user.id) \
        .order_by(VoucherBatch.created_at.desc()) \
        .all()

    return render_template("staff/dashboard.html", batches=my_batches)

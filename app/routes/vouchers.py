from flask import (
    Blueprint, render_template, redirect, url_for, flash, request, send_file
)
from flask_login import login_required, current_user
from datetime import datetime
import random, string
from io import BytesIO
import qrcode
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

from app.extensions import db
from app.forms.voucher_form import VoucherBatchForm
from app.models.voucher import Voucher
from app.models.voucher_batch import VoucherBatch
from app.models.router import MikroTikRouter
from app.models.plan import Plan
from app.utils.pdf_export import export_voucher_list_pdf
from app.utils.csv_export import export_voucher_list_csv
from app.services import MikroTikAPI

vouchers_bp = Blueprint("vouchers", __name__, url_prefix="/admin/vouchers")
lookup_bp = Blueprint("lookup", __name__, url_prefix="/support")


# ─────────────────────────────────────────
# 📄 View All Voucher Batches
# ─────────────────────────────────────────
@vouchers_bp.route("/batches", methods=["GET"])
@login_required
def view_batches():
    batches = VoucherBatch.query.order_by(VoucherBatch.created_at.desc()).all()
    return render_template("vouchers/batch_list.html", batches=batches)


# ─────────────────────────────────────────
# 🆕 Create a New Voucher Batch
# ─────────────────────────────────────────
@vouchers_bp.route("/new", methods=["GET", "POST"])
@login_required
def create_batch():
    form = VoucherBatchForm()
    form.set_router_choices()
    form.set_plan_choices()

    if form.validate_on_submit():
        # Handle custom or predefined plan
        if form.plan_id.data == "custom":
            new_plan = Plan(
                name="Custom Plan",
                bandwidth_limit_mb=form.custom_bandwidth.data,
                duration_days=form.custom_duration.data,
                price=form.custom_price.data or 0.00,
                created_at=datetime.utcnow()
            )
            db.session.add(new_plan)
            db.session.flush()
            plan_id = new_plan.id
        else:
            plan_id = int(form.plan_id.data)

        # Create VoucherBatch with valid plan_id
        batch = VoucherBatch(
            router_id=form.router_id.data,
            created_by_id=current_user.id,
            plan_id=plan_id,
            quantity=form.quantity.data,
            printed=False,
            created_at=datetime.utcnow()
        )
        db.session.add(batch)
        db.session.flush()

        # Load plan info (custom or selected)
        plan = Plan.query.get(plan_id)

        # Generate vouchers
        vouchers = [
            Voucher(
                code=generate_code(),
                plan_name=plan.name,
                bandwidth_limit_mb=plan.bandwidth_limit_mb,
                duration_days=plan.duration_days,
                type="offline",
                status="unused",
                router_id=batch.router_id,
                batch_id=batch.id,
                created_by_id=current_user.id,
                created_at=datetime.utcnow()
            )
            for _ in range(batch.quantity)
        ]

        db.session.add_all(vouchers)
        db.session.commit()

        # Attempt to sync vouchers to router
        router = batch.router
        router_api = MikroTikAPI(router.ip_address, router.api_username, router.api_password)
        if router_api.connect():
            router_api.upload_vouchers(vouchers)
            flash("✅ Vouchers auto-synced to MikroTik router.", "success")
        else:
            flash("⚠️ Vouchers created, but syncing to router failed.", "warning")

        return redirect(url_for("vouchers.view_batches"))

    return render_template("vouchers/create_batch.html", form=form)


# ─────────────────────────────────────────
# 🔁 Sync Vouchers to Router
# ─────────────────────────────────────────
@vouchers_bp.route("/batch/<int:batch_id>/sync")
@login_required
def sync_vouchers_to_router(batch_id):
    batch = VoucherBatch.query.get_or_404(batch_id)
    router = batch.router

    router_api = MikroTikAPI(router.ip_address, router.api_username, router.api_password)
    if not router_api.connect():
        flash("❌ Failed to connect to MikroTik router.", "danger")
        return redirect(url_for("vouchers.view_batches"))

    router_api.upload_vouchers(batch.vouchers.all())
    flash(f"✅ Vouchers synced successfully to router '{router.name}'.", "success")
    return redirect(url_for("vouchers.view_batches"))


# ─────────────────────────────────────────
# 📄 Export Batch to PDF (QR Codes)
# ─────────────────────────────────────────
@vouchers_bp.route("/batch/<int:batch_id>/export/pdf")
@login_required
def export_batch_pdf(batch_id):
    batch = VoucherBatch.query.get_or_404(batch_id)
    vouchers = batch.vouchers

    # Mark batch as printed
    batch.printed = True
    batch.printed_by_id = current_user.id
    batch.printed_at = datetime.utcnow()
    db.session.commit()

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    x = 50
    y = height - 50

    for v in vouchers:
        qr_img = qrcode.make(v.code)
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer)
        qr_buffer.seek(0)

        pdf.drawString(x, y, f"Voucher: {v.code} ({v.plan_name})")
        pdf.drawInlineImage(qr_buffer, x + 250, y - 20, 60, 60)

        y -= 80
        if y < 100:
            pdf.showPage()
            y = height - 50

    pdf.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True,
                     download_name=f"batch_{batch_id}.pdf",
                     mimetype='application/pdf')


# ─────────────────────────────────────────
# 📑 Export Batch to CSV
# ─────────────────────────────────────────
@vouchers_bp.route("/batch/<int:batch_id>/export/csv")
@login_required
def export_batch_csv(batch_id):
    batch = VoucherBatch.query.get_or_404(batch_id)
    vouchers = batch.vouchers
    csv_buffer = export_voucher_list_csv(vouchers)
    return send_file(csv_buffer, mimetype='text/csv',
                     as_attachment=True,
                     download_name=f'batch_{batch_id}.csv')


# ─────────────────────────────────────────
# 🔍 Voucher Lookup for Support
# ─────────────────────────────────────────
@lookup_bp.route("/voucher", methods=["GET", "POST"])
def check_voucher():
    voucher = None
    if request.method == "POST":
        code = request.form.get("code", "").strip().upper()
        if code:
            voucher = Voucher.query.filter_by(code=code).first()
    return render_template("support/voucher_lookup.html", voucher=voucher)


# ─────────────────────────────────────────
# 🧪 Utility: Code Generator
# ─────────────────────────────────────────
def generate_code(length=8):
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

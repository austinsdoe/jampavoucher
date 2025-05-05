# app/routes/admin/vouchers.py

from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, current_app
from flask_login import login_required, current_user
from io import BytesIO
from datetime import datetime, timedelta
import pandas as pd
import qrcode
import base64
import os

from app.forms.voucher_form import SingleVoucherForm
from app.forms.batch_form import VoucherBatchForm
from app.models import db, Voucher, VoucherBatch, Plan, MikroTikRouter
from app.services.mikrotik_api import MikroTikAPI
from app.utils.qr import generate_qr
from app.utils.voucher_generator import generate_voucher_codes
from app.utils.roles import role_required

voucher_bp = Blueprint("admin_vouchers", __name__, url_prefix="/admin")

# 🎟️ Create Single Voucher
@voucher_bp.route("/vouchers/create", methods=["GET", "POST"])
@login_required
@role_required("admin")
def create_voucher():
    form = SingleVoucherForm()
    form.set_plan_choices()
    form.set_router_choices()

    if form.validate_on_submit():
        code = form.code.data or generate_voucher_codes(1)[0]
        voucher = Voucher(
            code=code,
            plan_id=form.plan_id.data,
            router_id=form.router_id.data,
            type="offline",
            created_by_id=current_user.id
        )
        db.session.add(voucher)
        db.session.commit()
        generate_qr(code)
        flash("🎟️ Voucher created successfully!", "success")
        return redirect(url_for("admin.admin_vouchers.print_single_voucher", voucher_id=voucher.id))

    return render_template("admin/create_voucher.html", form=form)

# 🖨️ Print Single Voucher
@voucher_bp.route("/print-voucher/<int:voucher_id>")
@login_required
@role_required("admin")
def print_single_voucher(voucher_id):
    voucher = Voucher.query.get_or_404(voucher_id)
    voucher.qr_image = _generate_qr_base64(voucher.code)
    return render_template("admin/print_single_voucher.html", voucher=voucher)

# 🎟️ View Single Vouchers
@voucher_bp.route("/single-vouchers")
@login_required
@role_required("admin")
def single_vouchers():
    search = request.args.get("q", "").strip()
    router_filter = request.args.get("router", type=int)

    query = Voucher.query.filter_by(batch_id=None)
    if search:
        query = query.filter(Voucher.code.ilike(f"%{search}%"))
    if router_filter:
        query = query.filter_by(router_id=router_filter)

    vouchers = query.order_by(Voucher.created_at.desc()).all()
    routers = MikroTikRouter.query.order_by(MikroTikRouter.name.asc()).all()

    return render_template("admin/single_vouchers.html", vouchers=vouchers, routers=routers, search=search, selected_router=router_filter)

# 📦 Create Voucher Batch
@voucher_bp.route("/batches/create", methods=["GET", "POST"])
@login_required
@role_required("admin")
def create_voucher_batch():
    form = VoucherBatchForm()
    form.set_plan_choices()
    form.set_router_choices()

    if form.validate_on_submit():
        now = datetime.utcnow()
        quantity = form.quantity.data
        router_id = form.router_id.data
        created_by = current_user.id

        if form.plan_id.data == "custom":
            plan_name = f"Custom {form.custom_bandwidth.data}MB / {form.custom_duration.data}d"
            data_cap = form.custom_bandwidth.data
            duration_days = form.custom_duration.data
            price = float(form.custom_price.data or 0)
            plan_ref = None
        else:
            plan = Plan.query.get(int(form.plan_id.data))
            if not plan:
                flash("⚠️ Plan not found.", "danger")
                return render_template("admin/create_batch.html", form=form)
            plan_name = plan.name
            data_cap = plan.bandwidth_limit_mb
            duration_days = plan.duration_days
            price = plan.price
            plan_ref = plan.id

        batch = VoucherBatch(
            name=f"{plan_name} [{now.strftime('%Y-%m-%d %H:%M')}]",
            quantity=quantity,
            router_id=router_id,
            created_by_id=created_by,
            plan_id=plan_ref,
            created_at=now
        )
        db.session.add(batch)
        db.session.flush()

        codes = generate_voucher_codes(quantity)
        expires_at = now + timedelta(days=duration_days)

        for code in codes:
            voucher = Voucher(
                code=code,
                plan_id=plan_ref,
                plan_name=plan_name,
                batch_id=batch.id,
                router_id=router_id,
                created_by_id=created_by,
                status="unused",
                type="offline",
                data_cap=data_cap,
                price=price,
                created_at=now,
                expires_at=expires_at
            )
            db.session.add(voucher)
            generate_qr(code)

        db.session.commit()
        flash(f"📦 Created {quantity} vouchers in batch '{batch.name}'", "success")
        return redirect(url_for("admin.admin_vouchers.voucher_batches"))

    return render_template("admin/create_batch.html", form=form)

# 📦 List Voucher Batches
@voucher_bp.route("/batches")
@login_required
@role_required("admin")
def voucher_batches():
    search = request.args.get("q", "").strip()
    router_filter = request.args.get("router", type=int)
    upload_filter = request.args.get("upload")

    query = VoucherBatch.query

    if search:
        query = query.filter(VoucherBatch.name.ilike(f"%{search}%"))
    if router_filter is not None:
        query = query.filter_by(router_id=router_filter)
    if upload_filter == "uploaded":
        query = query.filter_by(upload_status="uploaded")
    elif upload_filter == "not_uploaded":
        query = query.filter(VoucherBatch.upload_status != "uploaded")

    batches = query.order_by(VoucherBatch.created_at.desc()).all()
    routers = MikroTikRouter.query.order_by(MikroTikRouter.name.asc()).all()
    return render_template("admin/voucher_batches.html", batches=batches, routers=routers, search=search, selected_router=router_filter)

# 📤 Upload Batch to Router
@voucher_bp.route("/batches/<int:batch_id>/upload", methods=["POST"])
@login_required
@role_required("admin")
def upload_batch_to_router(batch_id):
    batch = VoucherBatch.query.get_or_404(batch_id)
    if batch.upload_status == "uploaded":
        flash("⚠️ This batch has already been uploaded.", "warning")
        return redirect(url_for("admin.admin_vouchers.batch_detail", batch_id=batch.id))

    router = MikroTikRouter.query.get(batch.router_id)
    if not router:
        flash("❌ Router not found.", "danger")
        return redirect(url_for("admin.admin_vouchers.batch_detail", batch_id=batch.id))

    api = MikroTikAPI(router.ip_address, router.api_username, router.api_password, port=router.api_port)
    if not api.connect(router):
        flash("❌ Could not connect to router.", "danger")
        return redirect(url_for("admin.admin_vouchers.batch_detail", batch_id=batch.id))

    vouchers = Voucher.query.filter_by(batch_id=batch.id).all()

    try:
        api.upload_vouchers(vouchers, server="guest-hotspot")
        batch.upload_status = "uploaded"
        batch.upload_date = datetime.utcnow()
        db.session.commit()
        flash(f"✅ Uploaded {len(vouchers)} vouchers to router '{router.name}'.", "success")
    except Exception as e:
        flash(f"❌ Upload failed: {str(e)}", "danger")

    return redirect(url_for("admin.admin_vouchers.batch_detail", batch_id=batch.id))

# 📤 Upload Single Voucher
@voucher_bp.route("/vouchers/<int:voucher_id>/upload", methods=["POST"])
@login_required
@role_required("admin")
def upload_single_voucher(voucher_id):
    voucher = Voucher.query.get_or_404(voucher_id)
    if voucher.batch_id:
        flash("⚠️ This is part of a batch. Upload it from the batch page.", "warning")
        return redirect(url_for("admin.admin_vouchers.single_vouchers"))

    router = MikroTikRouter.query.get(voucher.router_id)
    if not router:
        flash("❌ Router not assigned.", "danger")
        return redirect(url_for("admin.admin_vouchers.single_vouchers"))

    api = MikroTikAPI(router.ip_address, router.api_username, router.api_password, port=router.api_port)
    if not api.connect(router):
        flash("❌ Router connection failed.", "danger")
        return redirect(url_for("admin.admin_vouchers.single_vouchers"))

    try:
        api.upload_vouchers([voucher], server="guest-hotspot")
        flash(f"✅ Uploaded voucher {voucher.code} to '{router.name}'", "success")
    except Exception as e:
        flash(f"❌ Upload failed: {str(e)}", "danger")

    return redirect(url_for("admin.admin_vouchers.single_vouchers"))

# 📦 View Batch Details
@voucher_bp.route("/batches/<int:batch_id>")
@login_required
@role_required("admin")
def batch_detail(batch_id):
    batch = VoucherBatch.query.get_or_404(batch_id)
    vouchers = Voucher.query.filter_by(batch_id=batch.id).order_by(Voucher.created_at.asc()).all()
    return render_template("admin/batch_detail.html", batch=batch, vouchers=vouchers)

# 🖨️ Print Batch
@voucher_bp.route("/batches/<int:batch_id>/print")
@login_required
@role_required("admin")
def print_batch(batch_id):
    batch = VoucherBatch.query.get_or_404(batch_id)
    vouchers = Voucher.query.filter_by(batch_id=batch.id).all()
    for v in vouchers:
        v.qr_image = _generate_qr_base64(v.code)
    return render_template("admin/print_batch.html", batch=batch, vouchers=vouchers)

# 📤 Export Batch
@voucher_bp.route("/batches/<int:batch_id>/export")
@login_required
@role_required("admin")
def export_batch(batch_id):
    batch = VoucherBatch.query.get_or_404(batch_id)
    vouchers = Voucher.query.filter_by(batch_id=batch.id).all()

    data = [{
        "Code": v.code,
        "Plan": v.plan_name,
        "Status": v.status,
        "Price (LRD)": v.price,
        "Expires At": v.expires_at.strftime("%Y-%m-%d"),
        "Created At": v.created_at.strftime("%Y-%m-%d %H:%M")
    } for v in vouchers]

    df = pd.DataFrame(data)
    file_path = os.path.join(current_app.config["DATA_DIR"], f"voucher_batch_{batch.id}.xlsx")
    df.to_excel(file_path, index=False)
    return send_file(file_path, as_attachment=True)

# 🧩 QR Code Utility
def _generate_qr_base64(data):
    img = qrcode.make(data)
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")

# 🗑️ Batch Deletion Endpoint
@voucher_bp.route("/delete-batches", methods=["POST"])
@login_required
@role_required("admin")
def delete_batches():
    batch_ids = request.form.getlist("batch_ids")
    if not batch_ids:
        flash("⚠️ No batches selected for deletion.", "warning")
        return redirect(url_for("admin.admin_vouchers.voucher_batches"))

    deleted = 0
    for batch_id in batch_ids:
        batch = VoucherBatch.query.get(batch_id)
        if batch:
            try:
                db.session.delete(batch)
                deleted += 1
            except Exception as e:
                print(f"[❌] Failed to delete batch {batch_id}: {e}")

    db.session.commit()
    flash(f"✅ Deleted {deleted} batch(es).", "success")
    return redirect(url_for("admin.admin_vouchers.voucher_batches"))

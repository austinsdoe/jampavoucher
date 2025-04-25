import csv
from io import BytesIO, StringIO
from flask import send_file
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
# app/utils/pdf_export.py
from io import BytesIO
from flask import send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def export_usage_pdf(vouchers):
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50

    pdf.setFont("Helvetica", 10)
    pdf.drawString(30, y, "Voucher Usage Report")
    y -= 30

    for v in vouchers:
        line = f"Code: {v.code} | Status: {v.status} | {v.bandwidth_limit_mb}MB | {v.duration_days}d | Used: {v.used_at or 'N/A'}"
        pdf.drawString(30, y, line)
        y -= 20
        if y < 50:
            pdf.showPage()
            y = height - 50

    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="voucher_usage.pdf", mimetype="application/pdf")


# ──────────────────────────────
# 📤 STAFF AUDIT REPORT (CSV)
# ──────────────────────────────
def export_staff_csv(staff_stats):
    """
    Export staff audit report as CSV.
    """
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Username', 'Vouchers Created', 'Batches Printed', 'Payments'])

    for s in staff_stats:
        writer.writerow([
            s.username,
            s.vouchers_created,
            s.batches_printed,
            s.payments_received
        ])

    output.seek(0)
    return send_file(
        BytesIO('\ufeff'.encode('utf-8') + output.getvalue().encode("utf-8")),
        mimetype="text/csv",
        as_attachment=True,
        download_name="staff_audit.csv"
    )


# ──────────────────────────────
# 💰 SALES REPORT (PDF)
# ──────────────────────────────
def export_sales_pdf(payments):
    """
    Export payment records as a clean paginated PDF.
    """
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(30, y, "Sales Report")
    y -= 30
    pdf.setFont("Helvetica", 9)

    for p in payments:
        line = f"{p.created_at.strftime('%Y-%m-%d')} | {p.amount} {p.currency or 'LRD'} | {p.provider.upper()} | {p.status} | {p.phone_number}"
        pdf.drawString(30, y, line)
        y -= 18
        if y < 50:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 9)

    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="sales_report.pdf", mimetype="application/pdf")


# ──────────────────────────────
# 📄 VOUCHER USAGE REPORT (PDF)
# ──────────────────────────────
def export_usage_to_pdf(usages):
    """
    Export voucher usage logs to PDF.
    """
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 50

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(30, y, "Voucher Usage Report")
    y -= 30
    pdf.setFont("Helvetica", 9)

    for u in usages:
        line = f"{u.mac_address or '-'} | {u.ip_address or '-'} | {u.voucher.code if u.voucher else '-'} | {u.session_start} → {u.session_end or '...'} | {u.data_used_mb or 0} MB"
        pdf.drawString(30, y, line)
        y -= 18
        if y < 50:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica", 9)

    pdf.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="voucher_usage.pdf", mimetype="application/pdf")


# ──────────────────────────────
# 🎟️ VOUCHER LIST EXPORT (PDF)
# ──────────────────────────────
def export_voucher_list_pdf(vouchers, title="Voucher List"):
    """
    Generate a nicely formatted voucher list PDF with columns.
    """
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    pdf.setTitle(title)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(40, height - 40, title)

    # Header
    y = height - 70
    headers = ["Code", "Plan", "Status", "Expires"]
    x_positions = [40, 200, 320, 430]
    pdf.setFont("Helvetica-Bold", 10)
    for i, h in enumerate(headers):
        pdf.drawString(x_positions[i], y, h)
    y -= 20
    pdf.setFont("Helvetica", 9)

    # Rows
    for v in vouchers:
        if y < 60:
            pdf.showPage()
            y = height - 50
            pdf.setFont("Helvetica-Bold", 10)
            for i, h in enumerate(headers):
                pdf.drawString(x_positions[i], y, h)
            y -= 20
            pdf.setFont("Helvetica", 9)

        pdf.drawString(x_positions[0], y, v.code)
        pdf.drawString(x_positions[1], y, v.plan_name)
        pdf.drawString(x_positions[2], y, v.status)
        pdf.drawString(x_positions[3], y, v.valid_until.strftime("%Y-%m-%d %H:%M") if v.valid_until else "-")
        y -= 15

    pdf.save()
    buffer.seek(0)
    return buffer  # to be returned via send_file() by the calling route

import csv
from io import StringIO, BytesIO
from flask import send_file
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


# ──────────────────────────────
# 📤 Staff Report Export (CSV)
# ──────────────────────────────
def export_staff_csv(staff_stats):
    """
    Exports a list of staff activity stats to CSV.
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
    return send_file(BytesIO('\ufeff'.encode('utf-8') + output.getvalue().encode("utf-8")),
                     mimetype="text/csv",
                     as_attachment=True,
                     download_name="staff_audit.csv")


# ──────────────────────────────
# 💰 Sales Report Export (CSV)
# ──────────────────────────────
def export_sales_csv(payments):
    """
    Exports payment records to CSV.
    """
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Amount', 'Provider', 'Phone', 'Status', 'Router', 'Paid By'])

    for p in payments:
        writer.writerow([
            p.created_at.strftime('%Y-%m-%d %H:%M'),
            p.amount,
            p.provider,
            p.phone_number,
            p.status,
            p.router.name if p.router else '',
            p.staff.username if getattr(p, "staff", None) else ''
        ])

    output.seek(0)
    return send_file(BytesIO('\ufeff'.encode('utf-8') + output.getvalue().encode("utf-8")),
                     mimetype="text/csv",
                     as_attachment=True,
                     download_name="sales_report.csv")


# ──────────────────────────────
# 📄 Voucher Usage (PDF)
# ──────────────────────────────
def export_usage_pdf(vouchers):
    """
    Generates a simple PDF voucher usage report.
    """
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
# 📤 Voucher Usage (CSV)
# ──────────────────────────────
def export_usage_to_csv(usages):
    """
    Exports detailed usage logs to CSV.
    """
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["MAC", "IP", "Voucher", "Start", "End", "Duration (min)", "MB Used"])

    for u in usages:
        writer.writerow([
            u.mac_address or '',
            u.ip_address or '',
            u.voucher.code if u.voucher else "-",
            u.session_start,
            u.session_end or '',
            getattr(u, "duration_minutes", ""),
            u.data_used_mb or ''
        ])

    output.seek(0)
    return send_file(BytesIO('\ufeff'.encode('utf-8') + output.getvalue().encode("utf-8")),
                     mimetype="text/csv",
                     as_attachment=True,
                     download_name="voucher_usage.csv")


# ──────────────────────────────
# 📦 Export Voucher List (CSV Only)
# ──────────────────────────────
def export_voucher_list_csv(vouchers):
    """
    Generates a raw CSV (not sent via `send_file`) of voucher records for batch download.
    """
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["Code", "Plan", "Status", "Expires"])

    for v in vouchers:
        writer.writerow([
            v.code,
            v.plan_name,
            v.status,
            v.valid_until.strftime("%Y-%m-%d %H:%M") if v.valid_until else "-"
        ])

    output.seek(0)
    return BytesIO(output.getvalue().encode('utf-8'))

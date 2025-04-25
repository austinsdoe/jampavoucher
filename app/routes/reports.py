from flask import Blueprint, render_template, request, send_file, flash
from datetime import datetime
from sqlalchemy import func, cast, Date
from app.extensions import db
from app.models import User, Voucher, Payment, MikroTikRouter, VoucherBatch, UserUsage

from io import StringIO, BytesIO
import csv
from openpyxl import Workbook
import matplotlib.pyplot as plt

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


# 📅 Date parsing helper
def parse_date(date_str, fallback=None):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return fallback


# 📤 XLSX export helper
def export_to_xlsx(data, headers, filename):
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in data:
        ws.append(row)
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')


# 💰 Sales Report
@reports_bp.route("/sales")
def sales_report():
    start = parse_date(request.args.get("start"))
    end = parse_date(request.args.get("end"))
    provider = request.args.get("provider")
    export_format = request.args.get("export")

    query = Payment.query.filter(Payment.status == "success")
    if start:
        query = query.filter(Payment.paid_at >= start)
    if end:
        query = query.filter(Payment.paid_at <= end)
    if provider:
        query = query.filter(Payment.provider == provider)

    payments = query.order_by(Payment.paid_at.desc()).limit(200).all()
    total_revenue = sum(p.amount for p in payments)

    if export_format == "csv":
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Transaction ID', 'Provider', 'Amount', 'Status', 'Voucher Code', 'Paid At'])
        for p in payments:
            writer.writerow([
                p.transaction_id, p.provider, p.amount,
                p.status, p.voucher.code if p.voucher else '',
                p.paid_at.strftime('%Y-%m-%d %H:%M') if p.paid_at else ''
            ])
        output.seek(0)
        return send_file(BytesIO(output.getvalue().encode()), download_name='sales_report.csv', mimetype='text/csv')

    if export_format == "xlsx":
        rows = [[
            p.transaction_id, p.provider, p.amount,
            p.status, p.voucher.code if p.voucher else '',
            p.paid_at.strftime('%Y-%m-%d %H:%M') if p.paid_at else ''
        ] for p in payments]
        return export_to_xlsx(rows, ['Transaction ID', 'Provider', 'Amount', 'Status', 'Voucher Code', 'Paid At'], 'sales_report.xlsx')

    return render_template("reports/sales_report.html", payments=payments, total=total_revenue)


# 📊 Usage Report
@reports_bp.route("/usage")
def usage_report():
    router_id = request.args.get("router_id")
    staff_id = request.args.get("staff_id")
    start = parse_date(request.args.get("start_date"))
    end = parse_date(request.args.get("end_date"))
    export_format = request.args.get("export")

    query = UserUsage.query
    if router_id:
        query = query.filter(UserUsage.router_id == router_id)
    if staff_id:
        query = query.filter(UserUsage.created_by_id == staff_id)
    if start:
        query = query.filter(UserUsage.session_start >= start)
    if end:
        query = query.filter(UserUsage.session_start <= end)

    usages = query.order_by(UserUsage.session_start.desc()).limit(100).all()

    if export_format == "csv":
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Voucher Code', 'Router', 'IP', 'MAC', 'Start', 'End', 'Duration (min)', 'Used MB'])
        for log in usages:
            writer.writerow([
                log.voucher_code, log.router.name if log.router else '',
                log.ip_address, log.mac_address or '',
                log.session_start, log.session_end or '',
                log.duration_minutes or '', log.data_used_mb or ''
            ])
        output.seek(0)
        return send_file(BytesIO(output.getvalue().encode()), download_name='voucher_usage.csv', mimetype='text/csv')

    elif export_format == "xlsx":
        rows = [[
            log.voucher_code, log.router.name if log.router else '',
            log.ip_address, log.mac_address or '',
            log.session_start, log.session_end or '',
            log.duration_minutes or '', log.data_used_mb or ''
        ] for log in usages]
        return export_to_xlsx(rows, ['Voucher Code', 'Router', 'IP', 'MAC', 'Start', 'End', 'Duration (min)', 'Used MB'], 'voucher_usage.xlsx')

    elif export_format == "pdf":
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter

        buffer = BytesIO()
        pdf = canvas.Canvas(buffer, pagesize=letter)
        pdf.setTitle("Voucher Usage Report")
        pdf.setFont("Helvetica-Bold", 14)
        pdf.drawString(40, 770, "Voucher Usage Report")
        y = 750
        pdf.setFont("Helvetica", 9)

        for log in usages:
            if y < 60:
                pdf.showPage()
                y = 770
            pdf.drawString(40, y, f"{log.voucher_code} | {log.router.name if log.router else ''} | {log.ip_address} | {log.session_start} | {log.data_used_mb or '-'}")
            y -= 15

        pdf.save()
        buffer.seek(0)
        return send_file(buffer, download_name='voucher_usage.pdf', mimetype='application/pdf')

    routers = MikroTikRouter.query.all()
    staff = User.query.filter_by(role="staff").all()
    return render_template("reports/usage_report.html", usages=usages, routers=routers, staff=staff)


# 👷 Staff Performance Report
@reports_bp.route("/staff")
def staff_report():
    export_format = request.args.get("export")

    query = db.session.query(
        User.id,
        User.username,
        func.count(Voucher.id).label("vouchers_created"),
        func.count(VoucherBatch.id).label("batches_printed"),
        func.count(Payment.id).label("payments_received")
    ).outerjoin(Voucher, Voucher.created_by_id == User.id) \
     .outerjoin(VoucherBatch, VoucherBatch.created_by_id == User.id) \
     .outerjoin(Payment, Payment.staff_id == User.id) \
     .filter(User.role == "staff") \
     .group_by(User.id, User.username)

    staff_stats = query.all()

    if export_format == "csv":
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Username', 'Vouchers Created', 'Batches Printed', 'Payments Received'])
        for s in staff_stats:
            writer.writerow([s.username, s.vouchers_created, s.batches_printed, s.payments_received])
        output.seek(0)
        return send_file(BytesIO(output.getvalue().encode()), download_name='staff_performance.csv', mimetype='text/csv')

    if export_format == "xlsx":
        rows = [[s.username, s.vouchers_created, s.batches_printed, s.payments_received] for s in staff_stats]
        return export_to_xlsx(rows, ['Username', 'Vouchers Created', 'Batches Printed', 'Payments Received'], 'staff_performance.xlsx')

    return render_template("reports/staff_report.html", staff_stats=staff_stats)


# 📊 Daily Bandwidth Usage Chart
@reports_bp.route("/daily-usage")
def daily_bandwidth_chart():
    export_format = request.args.get("export")

    usage_data = db.session.query(
        cast(UserUsage.session_start, Date).label("date"),
        func.sum(UserUsage.data_used_mb).label("total_mb")
    ).group_by("date").order_by("date").all()

    dates = [str(row.date) for row in usage_data]
    values = [float(row.total_mb or 0) for row in usage_data]

    if export_format == "csv":
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Date', 'Total Used MB'])
        for d, v in zip(dates, values):
            writer.writerow([d, v])
        output.seek(0)
        return send_file(BytesIO(output.getvalue().encode()), download_name='daily_usage.csv', mimetype='text/csv')

    elif export_format == "xlsx":
        rows = [[d, v] for d, v in zip(dates, values)]
        return export_to_xlsx(rows, ['Date', 'Total Used MB'], 'daily_usage.xlsx')

    # Generate PNG chart
    plt.figure(figsize=(10, 5))
    plt.bar(dates, values)
    plt.xlabel("Date")
    plt.ylabel("Data Used (MB)")
    plt.title("Daily Bandwidth Usage")
    plt.xticks(rotation=45)
    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    return send_file(buffer, mimetype="image/png", download_name="daily_usage_chart.png")

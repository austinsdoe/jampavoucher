# 📡 MikroTik Voucher Management System

A centralized hotspot voucher management platform for managing MikroTik routers, built with **Flask**, **PostgreSQL**, **Bootstrap 5**, and the **MikroTik API**.

This system enables admins and vendors to generate, print, and manage internet vouchers, sync with MikroTik routers, accept payments via Mobile Money or Stripe, and view real-time analytics.

---

## 🚀 Features

- 🔐 **Voucher-Based Login** for hotspot users
- 🧾 **Bulk Voucher Generation & Export (CSV/PDF)**
- 📊 **Dashboard Analytics & Reporting**
- 🌐 **Online Voucher Purchase with MTN / Orange / Stripe**
- 🔌 **MikroTik API Integration** for real-time sync
- 🛠 **Admin/Staff Roles with Permissions**
- 🔒 **Session Management** (IP/MAC lock, expiration)
- 🖨️ **Offline Voucher Printing with QR Codes**
- 📉 **Usage, Sales & Staff Reports**
- 🌍 **Multilingual Captive Portal with Branding**

---

## 🧰 Tech Stack

- **Backend:** Flask (Python), Flask-Login, Flask-Bootstrap, Jinja2
- **Frontend:** HTML5, Bootstrap 5, JavaScript
- **Database:** PostgreSQL (via SQLAlchemy)
- **Payment APIs:** MTN Mobile Money, Orange Money, Stripe
- **Router API:** MikroTik RouterOS API (via Python client)
- **Containerization:** Docker (optional)

---

## 🧪 Project Structure

jampavoucher/ │ ├── app/ # Main Flask app │ ├── routes/ # Blueprint routes │ ├── models/ # SQLAlchemy models │ ├── templates/ # Jinja2 HTML templates │ ├── static/ # CSS, JS, and assets │ └── services/ # Business logic and integrations │ ├── .env # Environment variables ├── run.py # Entry point ├── reset_db.py # DB reset script ├── requirements.txt # Python dependencies └── README.md # 
import stripe
import os
import uuid
from datetime import datetime
from app.extensions import db
from app.models.payment import Payment
from app.utils.voucher import create_online_voucher

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
BASE_URL = os.getenv("BASE_URL", "http://localhost:5000")


def create_stripe_checkout_session(amount_lrd):
    """
    Create a Stripe checkout session and save the payment record with a generated tx_id.
    """
    tx_id = str(uuid.uuid4())
    amount_usd = int(amount_lrd * 0.0055 * 100)  # Convert LRD to USD cents

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': 'Hotspot Voucher'},
                'unit_amount': amount_usd
            },
            'quantity': 1
        }],
        mode='payment',
        success_url=f"{BASE_URL}/payment/stripe-success?session_id={{CHECKOUT_SESSION_ID}}&tx_id={tx_id}",
        cancel_url=f"{BASE_URL}/payment"
    )

    # Save initial payment (status: pending)
    payment = Payment(
        transaction_id=tx_id,
        provider="stripe",
        amount=amount_lrd,
        currency="LRD",
        status="pending"
    )
    db.session.add(payment)
    db.session.commit()

    return session.url


def handle_stripe_success(session_id, tx_id):
    """
    Called after successful Stripe payment.
    Validates session and updates payment record.
    """
    session = stripe.checkout.Session.retrieve(session_id)
    if not session or session.payment_status != 'paid':
        return None

    # Find payment by our internal tx_id (not the Stripe session_id)
    payment = Payment.query.filter_by(transaction_id=tx_id).first()
    if not payment or payment.status == "success":
        return payment.voucher if payment else None

    payment.status = "success"
    payment.paid_at = datetime.utcnow()
    voucher = create_online_voucher(payment.amount)  # Use LRD amount
    payment.voucher = voucher
    db.session.commit()

    return voucher

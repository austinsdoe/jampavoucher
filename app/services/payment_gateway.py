import os
import uuid
import base64
import stripe
import requests
from datetime import datetime
from app.extensions import db
from app.models.payment import Payment


class PaymentGateway:
    def __init__(self):
        self.base_url = os.getenv("BASE_URL", "http://localhost:5000")

        # MTN Config
        self.mtn_api_url = "https://sandbox.momodeveloper.mtn.com/collection/v1_0"
        self.mtn_subscription_key = os.getenv("MTN_SUBSCRIPTION_KEY")
        self.mtn_environment = os.getenv("MTN_ENVIRONMENT", "sandbox")
        self.mtn_token = os.getenv("MTN_TOKEN")

        # Orange Config
        self.orange_api_url = "https://api.orange.com"
        self.orange_client_id = os.getenv("ORANGE_CLIENT_ID")
        self.orange_client_secret = os.getenv("ORANGE_CLIENT_SECRET")

        # Stripe Config
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

    def create_payment_record(self, tx_id, provider, phone, amount, currency="LRD", status="pending"):
        payment = Payment(
            transaction_id=tx_id,
            provider=provider,
            phone_number=phone,
            amount=amount,
            currency=currency,
            status=status,
            attempts=0,
            last_attempt_at=datetime.utcnow(),
            raw_response=None,
            error_message=None
        )
        db.session.add(payment)
        db.session.commit()
        return payment

    # --- ORANGE MONEY ---
    def get_orange_token(self):
        auth = f"{self.orange_client_id}:{self.orange_client_secret}".encode()
        headers = {
            "Authorization": "Basic " + base64.b64encode(auth).decode(),
            "Content-Type": "application/x-www-form-urlencoded"
        }
        data = {"grant_type": "client_credentials"}
        res = requests.post(f"{self.orange_api_url}/oauth/v3/token", headers=headers, data=data)
        return res.json().get("access_token") if res.status_code == 200 else None

    def initiate_orange_payment(self, phone, amount):
        tx_id = str(uuid.uuid4())
        token = self.get_orange_token()
        if not token:
            return None

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-Callback-Url": f"{self.base_url}/webhook/orange"
        }

        payload = {
            "amount": str(amount),
            "currency": "LRD",
            "external_id": tx_id,
            "payer": {"party_id_type": "MSISDN", "party_id": phone},
            "payer_message": "Hotspot Voucher",
            "payee_note": "Voucher Purchase"
        }

        requests.post(f"{self.orange_api_url}/omcore/1.0.0/payment/requesttopay", headers=headers, json=payload)
        self.create_payment_record(tx_id, "orange", phone, amount)
        return tx_id

    def verify_orange_payment(self, tx_id):
        token = self.get_orange_token()
        if not token:
            return False

        headers = {
            "Authorization": f"Bearer {token}",
            "X-Callback-Url": f"{self.base_url}/webhook/orange",
            "Content-Type": "application/json",
        }

        url = f"{self.orange_api_url}/orange-money-webpay/dev/v1/merchant/transactions/{tx_id}"
        response = requests.get(url, headers=headers)

        payment = Payment.query.filter_by(transaction_id=tx_id).first()
        if payment:
            payment.attempts += 1
            payment.last_attempt_at = datetime.utcnow()

        if response.status_code == 200:
            result = response.json()
            if payment:
                payment.raw_response = result
            status = result.get("status", "").upper()
            if status == "SUCCESSFUL":
                if payment:
                    payment.status = "success"
                    db.session.commit()
                return True
            elif status == "FAILED":
                if payment:
                    payment.status = "failed"
                    payment.error_message = result.get("message", "Payment failed")
                    db.session.commit()
                return False
            else:
                return None  # pending
        else:
            if payment:
                payment.error_message = f"HTTP {response.status_code}"
                db.session.commit()
            return False

    # --- MTN MOBILE MONEY ---
    def mtn_headers(self, reference_id=None):
        headers = {
            "X-Target-Environment": self.mtn_environment,
            "Ocp-Apim-Subscription-Key": self.mtn_subscription_key,
            "Authorization": f"Bearer {self.mtn_token}",
            "Content-Type": "application/json"
        }
        if reference_id:
            headers["X-Reference-Id"] = reference_id
        return headers

    def initiate_mtn_payment(self, phone, amount):
        tx_id = str(uuid.uuid4())
        payer = {"partyIdType": "MSISDN", "partyId": phone}
        payload = {
            "amount": str(amount),
            "currency": "LRD",
            "externalId": tx_id,
            "payer": payer,
            "payerMessage": "Hotspot Voucher",
            "payeeNote": "Voucher Purchase"
        }

        headers = self.mtn_headers(reference_id=tx_id)
        url = f"{self.mtn_api_url}/requesttopay"

        res = requests.post(url, json=payload, headers=headers)
        if res.status_code in [200, 202]:
            self.create_payment_record(tx_id, "mtn", phone, amount)
            return tx_id
        else:
            raise Exception(f"MTN payment initiation failed: {res.text}")

    def verify_mtn_payment(self, tx_id):
        headers = self.mtn_headers()
        url = f"{self.mtn_api_url}/requesttopay/{tx_id}"

        response = requests.get(url, headers=headers)

        payment = Payment.query.filter_by(transaction_id=tx_id).first()
        if payment:
            payment.attempts += 1
            payment.last_attempt_at = datetime.utcnow()

        if response.status_code == 200:
            result = response.json()
            if payment:
                payment.raw_response = result
            status = result.get("status", "").lower()
            if status == "success":
                if payment:
                    payment.status = "success"
                    db.session.commit()
                return True
            elif status == "failed":
                if payment:
                    payment.status = "failed"
                    payment.error_message = result.get("reason", "Transaction failed")
                    db.session.commit()
                return False
            else:
                return None
        else:
            if payment:
                payment.error_message = f"MTN HTTP {response.status_code}"
                db.session.commit()
            return False

    # --- STRIPE PAYMENTS ---
    def create_stripe_checkout_session(self, amount_lrd):
        tx_id = str(uuid.uuid4())
        self.create_payment_record(tx_id, "stripe", None, amount_lrd)

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "lrd",
                    "product_data": {"name": "Hotspot Voucher"},
                    "unit_amount": int(float(amount_lrd) * 100),
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"{self.base_url}/payment/stripe-success?tx_id={tx_id}&session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{self.base_url}/payment/"
        )
        return checkout_session.url

    def handle_stripe_success(self, session_id, tx_id):
        from app.utils.voucher import create_online_voucher
        session = stripe.checkout.Session.retrieve(session_id)
        if session and session.payment_status == "paid":
            return create_online_voucher(tx_id)
        return None

    # --- Unified Verifier ---
    def verify_payment_and_create_voucher(self, tx_id):
        from app.utils.voucher import create_online_voucher
        payment = Payment.query.filter_by(transaction_id=tx_id).first()
        if payment and payment.status == "paid":
            return create_online_voucher(tx_id)
        return None

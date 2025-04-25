# app/utils/voucher_generator.py

import secrets
import string
from datetime import datetime, timedelta
from typing import List
from app.extensions import db
from app.models.voucher import Voucher
from app.models.plan import Plan


def generate_code(length: int = 10) -> str:
    """
    Generate a secure random alphanumeric code.
    """
    characters = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


def generate_unique_code(length: int = 10, retries: int = 20) -> str:
    """
    Generate a secure voucher code that does not already exist in the DB.
    """
    for _ in range(retries):
        code = generate_code(length)
        if not Voucher.query.filter_by(code=code).first():
            return code
    raise ValueError("❌ Failed to generate a unique voucher code after multiple attempts.")


def generate_voucher_codes(quantity: int = 1, length: int = 10) -> List[str]:
    """
    Generate a list of unique voucher codes.
    """
    codes = set()
    while len(codes) < quantity:
        codes.add(generate_unique_code(length=length))
    return list(codes)


def create_online_voucher(amount: float) -> Voucher:
    """
    Create an online voucher based on payment amount using the Plan model.
    Sets expiration and other attributes based on plan settings.
    """
    # Match amount to plan
    if amount < 20:
        plan = Plan.query.filter_by(name="Basic 1500MB").first()
    elif amount < 40:
        plan = Plan.query.filter_by(name="Standard 3000MB").first()
    elif amount < 60:
        plan = Plan.query.filter_by(name="Pro 5000MB").first()
    else:
        plan = Plan.query.filter_by(name="Max 10000MB").first()

    if not plan:
        raise LookupError(f"❌ No matching plan found for amount: {amount}")

    now = datetime.utcnow()
    expires_at = now + timedelta(days=plan.duration)

    voucher = Voucher(
        code=generate_unique_code(),
        plan_id=plan.id,
        status="unused",
        type="online",
        created_at=now,
        expires_at=expires_at,
        data_cap=plan.data_limit
    )
    db.session.add(voucher)
    db.session.commit()

    print(f"[VOUCHER] ✅ Created {voucher.code} - {plan.name} ({plan.data_limit}MB for {plan.duration} days)")
    return voucher

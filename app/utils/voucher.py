import secrets
import string
from datetime import datetime, timedelta

from app.models.voucher import Voucher
from app.models.plan import Plan
from app.models import MikroTikRouter
from app.extensions import db
from app.services.mikrotik_api import MikroTikAPI


def cleanup_expired_vouchers():
    """
    Remove expired vouchers from MikroTik router (hotspot users + queues).
    Intended to run as a scheduled task (e.g. via Celery or CLI).
    """
    expired = Voucher.query.filter(
        (Voucher.status == "expired") |
        (Voucher.valid_until < datetime.utcnow())
    ).all()

    for v in expired:
        router = MikroTikRouter.query.get(v.router_id)
        if router:
            api = MikroTikAPI(router.ip, router.username, router.password, router.api_port)
            if api.connect():
                # Remove hotspot user
                try:
                    user_res = api.api.get_resource("/ip/hotspot/user")
                    users = user_res.get(name=v.code)
                    for user in users:
                        user_res.remove(id=user[".id"])
                        print(f"[🧹] Removed expired hotspot user: {v.code}")
                except Exception as e:
                    print(f"[❌] Error removing user {v.code}: {e}")

                # Remove queue
                try:
                    queue_res = api.api.get_resource("/queue/simple")
                    queues = queue_res.get(name=f"queue_{v.code}")
                    for q in queues:
                        queue_res.remove(id=q[".id"])
                        print(f"[🧹] Removed queue: queue_{v.code}")
                except Exception as e:
                    print(f"[❌] Error removing queue for {v.code}: {e}")


def generate_code(length: int = 10) -> str:
    """
    Securely generate a random alphanumeric voucher code.
    """
    characters = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


def generate_unique_code(length: int = 10, retries: int = 10) -> str:
    """
    Generate a voucher code that does not already exist in the database.
    """
    for _ in range(retries):
        code = generate_code(length)
        if not Voucher.query.filter_by(code=code).first():
            return code
    raise ValueError("❌ Failed to generate a unique voucher code after multiple attempts.")


def create_online_voucher(amount: float) -> Voucher:
    """
    Create a voucher based on the best matching plan for the given payment amount.
    Automatically sets expiration and data cap from the plan.
    """
    plan = Plan.query.filter(Plan.price <= amount).order_by(Plan.price.desc()).first()

    if not plan:
        raise LookupError(f"❌ No matching plan found for amount: {amount}")

    now = datetime.utcnow()
    expires_at = now + timedelta(days=plan.duration or 1)

    voucher = Voucher(
        code=generate_unique_code(),
        plan_id=plan.id,
        status="unused",
        type="online",
        created_at=now,
        activated_at=None,
        expires_at=expires_at,
        data_cap=plan.data_limit
    )

    db.session.add(voucher)
    db.session.commit()

    print(f"[VOUCHER] ✅ Created {voucher.code} - {plan.name} ({plan.data_limit}MB, {plan.duration}d)")
    return voucher

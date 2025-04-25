import click
from datetime import datetime, timedelta
from app.extensions import db
from app.models import Voucher, UserUsage, MikroTikRouter
from app.services.mikrotik_api import MikroTikAPI

@click.command("cleanup-expired")
def cleanup_expired():
    """Deactivate expired vouchers and clean up expired sessions."""
    now = datetime.utcnow()

    # ── Step 1: Expire vouchers
    expired = Voucher.query.filter(
        Voucher.expires_at < now,
        Voucher.status == "unused"
    ).all()

    for v in expired:
        v.status = "expired"
        print(f"❌ Expired voucher: {v.code}")

    db.session.commit()

    # ── Step 2: Sync active vouchers to routers (optional)
    active_usages = UserUsage.query.filter_by(active=True).all()
    for usage in active_usages:
        voucher = Voucher.query.get(usage.voucher_id)
        if not voucher:
            continue

        router = MikroTikRouter.query.get(voucher.router_id)
        if not router:
            print(f"[⚠️] Router not found for voucher {voucher.code}")
            continue

        api = MikroTikAPI(router.ip, router.username, router.password, router.api_port)
        if not api.connect():
            print(f"[⚠️] Could not connect to router {router.name}")
            continue

        profile_name = voucher.plan_name or "default"
        try:
            api.add_hotspot_user(
                name=voucher.code,
                password="",
                limit_bytes_total=voucher.data_cap * 1024 * 1024,
                profile=profile_name
            )
            print(f"[✅] Synced Hotspot User: {voucher.code}")
        except Exception as e:
            print(f"[⚠️] Hotspot user sync failed: {e}")

        if voucher.plan and voucher.plan.rate_limit:
            queue_limit = voucher.plan.rate_limit
        else:
            print(f"[⚠️] No rate limit found in plan, using default for {voucher.code}")
            queue_limit = "1M/1M"

        if not usage.ip_address or not usage.ip_address.strip():
            print(f"[⚠️] Skipping queue for {voucher.code} (no IP found)")
            continue

        try:
            api.create_simple_queue(
                name=f"queue_{voucher.code}",
                target=usage.ip_address,
                max_limit=queue_limit
            )
            print(f"[✅] Queue created for: {voucher.code}")
        except Exception as e:
            print(f"[⚠️] Queue creation failed for {voucher.code}: {e}")

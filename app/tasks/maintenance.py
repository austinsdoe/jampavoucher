from app import create_app
from app.utils.voucher_generator import cleanup_expired_vouchers
from app.tasks.celery_worker import celery

@celery.task
def run_expired_voucher_cleanup():
    app = create_app()
    with app.app_context():
        cleanup_expired_vouchers()

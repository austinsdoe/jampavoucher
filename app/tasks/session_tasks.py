from datetime import datetime, timedelta
from app import create_app
from app.extensions import db
from app.models.user_usage import UserUsage
from app.tasks.celery_worker import celery

@celery.task
def cleanup_stale_sessions():
    app = create_app()
    with app.app_context():
        cutoff = datetime.utcnow() - timedelta(minutes=30)

        stale_sessions = UserUsage.query.filter(
            UserUsage.session_end.is_(None),
            UserUsage.session_start < cutoff
        ).all()

        for session in stale_sessions:
            session.session_end = datetime.utcnow()
            session.duration_minutes = round((session.session_end - session.session_start).total_seconds() / 60)
            session.timed_out = True
            print(f"[TIMEOUT] ⏱️ Session auto-closed: {session.voucher_code} (started at {session.session_start})")

        db.session.commit()

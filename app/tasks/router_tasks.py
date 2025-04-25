from datetime import datetime
from app import create_app
from app.extensions import db
from app.models.router import MikroTikRouter
from app.services.mikrotik_api import MikroTikAPI
from app.tasks.celery_worker import celery


@celery.task
def sync_router_status():
    app = create_app()
    with app.app_context():
        routers = MikroTikRouter.query.all()
        for router in routers:
            api = MikroTikAPI(router.ip, router.username, router.password, router.api_port)
            reachable = api.ping()
            router.last_ping = datetime.utcnow()
            router.online = reachable
            try:
                if reachable:
                    if not api.api:
                        api.connect()
                    uptime = api.get_uptime()
                    router.uptime = uptime
                    api.log_action("Fetched uptime", {"uptime": uptime})
                else:
                    api.log_action("Router offline")
            except Exception as e:
                api.handle_error("fetch uptime", e)

        db.session.commit()

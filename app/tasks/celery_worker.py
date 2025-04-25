from celery import Celery
from dotenv import load_dotenv
import os

load_dotenv()

def make_celery(app_name=__name__):
    broker = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
    backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
    return Celery(app_name, broker=broker, backend=backend)

celery = make_celery("jampavoucher")

# Discover tasks from this package
celery.autodiscover_tasks(["app.tasks"])

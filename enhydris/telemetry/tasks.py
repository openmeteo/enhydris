from django.core.cache import cache

from celery.utils.log import get_task_logger

from enhydris.celery import app
from enhydris.telemetry.models import Telemetry

FETCH_TIMEOUT = 300
LOCK_TIMEOUT = FETCH_TIMEOUT + 60

logger = get_task_logger(__name__)


@app.task
def fetch_all_telemetry_data():
    for telemetry in Telemetry.objects.all():
        if telemetry.is_due:
            fetch_telemetry_data.delay(telemetry.id)


@app.task(bind=True, soft_time_limit=FETCH_TIMEOUT, time_limit=FETCH_TIMEOUT + 10)
def fetch_telemetry_data(self, telemetry_id):
    telemetry = Telemetry.objects.get(id=telemetry_id)
    lock_id = f"telemetry-{telemetry_id}"
    acquired_lock = cache.add(lock_id, self.app.oid, LOCK_TIMEOUT)
    if acquired_lock:
        try:
            telemetry.fetch()
        finally:
            cache.delete(lock_id)
    else:
        lock_owner = cache.get(lock_id)
        logger.error(
            f"Cannot acquire lock for fetching telemetry with id={telemetry.id}; "
            f"apparently the lock is owned by {lock_owner}."
        )

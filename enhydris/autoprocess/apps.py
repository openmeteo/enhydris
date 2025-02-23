from django.apps import AppConfig
from django.db import transaction
from django.db.models.signals import post_save

from .tasks import execute_auto_process


def enqueue_auto_process(sender, *, instance, **kwargs):
    auto_processes = [
        auto_process
        for auto_process in instance.timeseries_group.autoprocess_set.all()
        if auto_process.as_specific_instance.source_timeseries == instance
    ]
    for auto_process in auto_processes:
        transaction.on_commit(lambda: execute_auto_process.delay(auto_process.id))


class AutoprocessConfig(AppConfig):
    name = "enhydris.autoprocess"

    def ready(self):
        post_save.connect(enqueue_auto_process, sender="enhydris.Timeseries")

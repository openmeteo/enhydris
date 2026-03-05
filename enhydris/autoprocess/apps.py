from django.apps import AppConfig
from django.db import transaction
from django.db.models.signals import post_save

from .tasks import execute_auto_process


def enqueue_auto_process(sender, *, instance, **kwargs):
    def enqueue_on_commit(auto_process_id: int, has_non_append_modifications: bool):
        transaction.on_commit(
            lambda: execute_auto_process.delay(
                auto_process_id, has_non_append_modifications
            )
        )

    auto_processes = [
        auto_process
        for auto_process in instance.timeseries_group.autoprocess_set.all()
        if auto_process.as_specific_instance.source_timeseries == instance
    ]
    for auto_process in auto_processes:
        enqueue_on_commit(auto_process.id, instance.has_non_append_modifications)


class AutoprocessConfig(AppConfig):
    name = "enhydris.autoprocess"

    def ready(self):
        post_save.connect(enqueue_auto_process, sender="enhydris.Timeseries")

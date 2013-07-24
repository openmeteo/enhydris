from django.core.management.base import BaseCommand, CommandError
from enhydris.hrain import models

class Command(BaseCommand):
    args = ''
    help = """Recalculates all rain events.

When you run this command, all enhydris.hrain.Event will be deleted,
and the rainfall events will be recalculated. Useful for running from
cron periodically to refresh enhydris.hrain.Event."""

    def handle(self, *args, **options):
        models.refresh_events()

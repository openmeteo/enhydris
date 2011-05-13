from django.core.management.base import BaseCommand, CommandError
import django.db
from enhydris.hcore.tstmpupd import update_ts_temp_file
from enhydris.hprocessor.models import (ProcessBatch, ProcessUnit,
                                        ProcessInputVariable) 
from pthelma.tsprocess import (MultiTimeseriesProcessDb,
                               AggregateDbTimeseries) 
from django.conf import settings


def ts_cache_update(id):
    if hasattr(settings, 'TS_GRAPH_CACHE_DIR'):
        cache_dir = settings.TS_GRAPH_CACHE_DIR
    else:
        cache_dir = '/var/tmp/enhydris-timeseries/'
    update_ts_temp_file(cache_dir, django.db.connection, id)


def process_batch(batch):
    jobs = ProcessUnit.objects.filter(batch__id=batch.id)
    jobs = jobs.order_by('order')
    for job in jobs:
        if job.method == 'Tsupdate':
            ts_cache_update(job.output_timeseries.id)
        else:
            assert(False)


class Command(BaseCommand):
    args = '<batch_name batch_name ...>'
    help = """Running processing batches defined
              with the hprocessor administrative
              interface. Call with the unique_name
              parameter as argument."""

    def handle(self, *args, **options):
        for batch_name in args:
            try:
                batch = ProcessBatch.objects.get(unique_name=batch_name)
                process_batch(batch)
            except ProcessBatch.DoesNotExist:
                raise CommandError('Batch "%s" does not exist' %(batch_name,))



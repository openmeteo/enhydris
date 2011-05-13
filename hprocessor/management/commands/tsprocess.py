import os
from django.core.management.base import BaseCommand, CommandError
from django import db
from enhydris.hcore.tstmpupd import update_ts_temp_file
from enhydris.hcore.models import ReadTimeStep
from enhydris.hprocessor.models import (ProcessBatch, ProcessUnit,
                                        ProcessInputVariable) 
from pthelma.tsprocess import (MultiTimeseriesProcessDb,
                               AggregateDbTimeseries) 
from django.conf import settings


@db.transaction.commit_on_success
def ts_aggregation(job):
    job_var = ProcessInputVariable.objects.all()[0]
    AggregateDbTimeseries(source_id=job_var.timeseries.id, 
                          dest_id=job.output_timeseries.id, 
                          db=db.connection, transaction=db.transaction,
                          read_tstep_func=ReadTimeStep,
                          missing_allowed=job.aggregation_missing_allowed,
                          missing_flag=job.aggregation_missing_flag,
                          append_only=job.append_only)
    if not job.append_only:
        if hasattr(settings, 'TS_GRAPH_CACHE_DIR'):
            cache_dir = settings.TS_GRAPH_CACHE_DIR
        else:
            cache_dir = '/var/tmp/enhydris-timeseries/'
        afilename = os.path.join(cache_dir, 
                                 '%d.hts'%int(job.output_timeseries.id))
        if os.path.exists(afilename):
            os.remove(afilename)


def ts_cache_update(id):
    if hasattr(settings, 'TS_GRAPH_CACHE_DIR'):
        cache_dir = settings.TS_GRAPH_CACHE_DIR
    else:
        cache_dir = '/var/tmp/enhydris-timeseries/'
    update_ts_temp_file(cache_dir, db.connection, id)


def process_batch(batch):
    jobs = ProcessUnit.objects.filter(batch__id=batch.id)
    jobs = jobs.order_by('order')
    for job in jobs:
        if job.method in ('HeatIndex', 'SSI', 'IDM_monthly',
                          'IDM_annual', ):
            pass
        elif job.method == 'Aggregation':
            ts_aggregation(job)
        elif job.method == 'Tsupdate':
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



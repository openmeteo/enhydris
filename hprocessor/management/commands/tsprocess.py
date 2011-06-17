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


def get_cache_dir():
    if hasattr(settings, 'TS_GRAPH_CACHE_DIR'):
        return settings.TS_GRAPH_CACHE_DIR
    else:
        return '/var/tmp/enhydris-timeseries/'


def clear_timeseries_cache(timeseries_id):
    afilename = os.path.join(get_cache_dir(),
                             '%d.hts'%int(timeseries_id))
    if os.path.exists(afilename):
        os.remove(afilename)


@db.transaction.commit_on_success
def multi_ts_process(job):
    job_vars = ProcessInputVariable.objects.filter(process_unit__id=job.id)
    timeseries_arg = {}
    for job_var in job_vars:
        timeseries_arg[job_var.spec] = job_var.timeseries.id
    options = {}
    if job.append_only:
        options['append_only']=True
    if job.method == 'BaromFormula':
        options['hdiff'] = job.aggregation_missing_allowed
    MultiTimeseriesProcessDb(method=job.method, timeseries_arg=timeseries_arg, 
                             out_timeseries_id=job.output_timeseries.id,
                             db=db.connection, transaction=db.transaction,
                             options=options)
    if not job.append_only:
        clear_timeseries_cache(job.output_timeseries.id)


@db.transaction.commit_on_success
def ts_aggregation(job):
    job_var = ProcessInputVariable.objects.filter(process_unit__id=job.id)[0]
    AggregateDbTimeseries(source_id=job_var.timeseries.id, 
                          dest_id=job.output_timeseries.id, 
                          db=db.connection, transaction=db.transaction,
                          read_tstep_func=ReadTimeStep,
                          missing_allowed=job.aggregation_missing_allowed,
                          missing_flag=job.aggregation_missing_flag,
                          append_only=job.append_only)
    if not job.append_only:
        clear_timeseries_cache(job.output_timeseries.id)


def ts_cache_update(id):
    update_ts_temp_file(get_cache_dir(), db.connection, id)


def process_batch(batch):
    jobs = ProcessUnit.objects.filter(batch__id=batch.id)
    jobs = jobs.order_by('order')
    for job in jobs:
        if job.method in ('HeatIndex', 'SSI', 'IDM_monthly',
                          'IDM_annual', 'BaromFormula' ):
            multi_ts_process(job)
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

import os
from django.core.management.base import BaseCommand, CommandError
from django import db
from datetime import datetime
from optparse import make_option
from enhydris.hcore.tstmpupd import update_ts_temp_file
from enhydris.hcore.models import ReadTimeStep
from enhydris.hprocessor.models import (ProcessBatch, ProcessUnit,
                                        ProcessInputVariable) 
from pthelma.tsprocess import (MultiTimeseriesProcessDb,
                               AggregateDbTimeseries,
                               InterpolateDbTimeseries) 
from enhydris.conf import settings


def clear_timeseries_cache(timeseries_id):
    afilename = os.path.join(settings.ENHYDRIS_TS_GRAPH_CACHE_DIR,
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
                             read_tstep_func=ReadTimeStep, options=options)
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
                          append_only=job.append_only,
                          last_incomplete=job.aggregation_last_incomplete,
                          all_incomplete=job.aggregation_all_incomplete)
    if not job.append_only:
        clear_timeseries_cache(job.output_timeseries.id)


@db.transaction.commit_on_success
def ts_interpolation(job):
    job_var = ProcessInputVariable.objects.filter(process_unit__id=job.id)[0]
    InterpolateDbTimeseries(source_id=job_var.timeseries.id, 
                            dest_id=job.output_timeseries.id, 
                            db=db.connection, transaction=db.transaction,
                            curve_type=job.interpol_method,
                            curve_data=str(job.curve.content),
                            data_columns=(job.independent_column,
                                          job.dependent_column),
                            logarithmic=job.aggregation_last_incomplete,
                            offset=job.aggregation_missing_allowed,
                            append_only=job.append_only)
    if not job.append_only:
        clear_timeseries_cache(job.output_timeseries.id)


def ts_cache_update(id):
    update_ts_temp_file(settings.ENHYDRIS_TS_GRAPH_CACHE_DIR, db.connection, id)


def process_batch(batch, **options):
    jobs = ProcessUnit.objects.filter(batch__id=batch.id)
    jobs = jobs.order_by('order')
    stout = options['handle'].stdout #should use this one instead of
                                     #stdout
    if options['verbosity']=='2' and options['refresh']==True:
        stout.write('Full refresh of time series requested.\n'
                    'All append_only settings will be overiden '
                    'to "False"\n\n')
    start_time = datetime.now()
    for job in jobs:
        if options['refresh']==True:
            job.append_only=False
        if options['verbosity']=='2':
            stout.write('Processing job id=%d, name: "%s", '
                        'method: "%s", order=%d. '%(job.id, 
                                    job.name, job.method, job.order))
            stout.write('Append only setting for this job '
                        'is "%s"\n'%(job.append_only,))
        if job.method in ('HeatIndex', 'SSI', 'IDM_monthly',
                          'IDM_annual', 'BaromFormula',
                          'OneStepDiff' ):
            multi_ts_process(job)
        elif job.method == 'Aggregation':
            ts_aggregation(job)
        elif job.method == 'Interpolation':
            ts_interpolation(job)
        elif job.method == 'Tsupdate':
            ts_cache_update(job.output_timeseries.id)
        else:
            assert(False)
    end_time = datetime.now()
    if options['verbosity']=='2':
        stout.write('End of processing, time elapsed=%s'
                    '\n\n'%(end_time-start_time,))


class Command(BaseCommand):
    args = '<batch_name batch_name ...>'
    help = 'Running processing batches defined '\
           'with the hprocessor administrative '\
           'interface. Call with the unique_name '\
           'parameter as argument.'

    option_list = BaseCommand.option_list + (
        make_option('--refresh', '-r',
            action='store_true',
            dest='refresh',
            default='False',
            help='Refresh output timeseries by an explicit full write '
                 'whatever is the append_only setting is. Running the '
                 'process with refreshing, acts like append_only=File'),
        )
    def handle(self, *args, **options):
        options['handle'] = self
        for batch_name in args:
            try:
                batch = ProcessBatch.objects.get(unique_name=batch_name)
                process_batch(batch, **options)
            except ProcessBatch.DoesNotExist:
                raise CommandError('Batch "%s" does not exist' %(batch_name,))

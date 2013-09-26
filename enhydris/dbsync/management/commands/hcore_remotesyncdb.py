"""
Management command which takes care of syncing the master db
"""

import datetime
import inspect
import os
import re
import signal
import sys
import threading
import urllib2
import json
from optparse import make_option
from socket import socket, gethostbyname, AF_INET, SOCK_STREAM

from django.core import serializers
from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.db import models as dj_models
from django.db.models import get_app
from django.utils.http import urlquote

from enhydris.dbsync.models import Database


# Register a signal to catch kbd interrupts and handle them
def signal_handler(signal, frame):
    """
    Signal handler for keyboard interrupts (ctrl+C)
    """
    MSG("Keyboard Interrupt received. Aborting...")
    gracefull_exit(1)
signal.signal(signal.SIGINT, signal_handler)


def gracefull_exit(status):
    """
    This handles system cleanup in case of an exception or user given
    interrupt.
    """
    # Ignore any more signals (HUP mostly)
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    # Get object list
    onames = [ f for f in globals().keys() if re.match("^Generic.*", f) ]
    onames.sort(reverse=True)

    transaction.commit_unless_managed()
    transaction.enter_transaction_management()
    transaction.managed(True)
    # delete the objects
    for object in onames:
        try:
            exec(object+'.delete()')
        except Exception, detail:
            pass

    transaction.commit()
    transaction.leave_transaction_management()

    # exit
    sys.exit(status)


# This dict holds all outstanding foreign key relations that could not be added
# during the first transaction. This wil be parsed after the main transaction
# is commited and all objects are saved in the local db

batch_jobs = {}


# A progress indicator just for presentation
class RotatingThing(threading.Thread):
    """
    This is a progress indicator which displays a rotating thing.
    """
    def __init__(self, msg):
        threading.Thread.__init__(self)
        self.msg = msg
        self.array = '-\|/'
        self.current = 0
        self.event = threading.Event()
    def __enter__(self):
        self.start()
    def __exit__(self, ex_type, ex_value, ex_traceback):
        self.event.set()
        sys.stdout.write("\b: done\n")
        self.join()
    def run(self):
        """
        This is the function that gets executed when the thread starts
        """
        sys.stdout.write(self.msg)
        while not self.event.isSet():
            sys.stdout.write("\b%s" % self.array[self.current % \
                                    len(self.array)])
            self.current += 1
            sys.stdout.flush()
            self.event.wait(0.5)


def check_remote(remote, port):
    """
    Given a hostname/ip and a port number, the function checks to see if there
    is any application listening at the other side of the connection.
    """

    # Get host ip
    if not re.match('(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25'\
                    '[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)', remote):
        try:
            remoteIP = gethostbyname(remote)
        except:
            ERRMSG('Remote address doesn\'t seem valid. Make sure you used'\
                   ' a valid address and that the remote server is running')
            gracefull_exit(1)
    else:
        ERRMSG('Please provide a FQDN for the remote instance and not just'\
               ' the ip. Exiting...')
        gracefull_exit(1)
    # Get port
    try:
        port = int(port)
        if port <= 0 or port > 65536:
            raise Exception
    except:
        ERRMSG('The port you have specified doesn\'t seem to be valid.')
        return False

    # Check if host is accessible
    MSG('Checking port availability on host %s, port %s' % (remoteIP, port))
    s = socket(AF_INET, SOCK_STREAM)
    try:
        s.connect((remoteIP, port))
    except:
        s.close()
        return False

    s.close()
    return True


def get_models(app, exc_list=None):
    """
    This function returns a list of models given a specific application.

    To do this, we take the app name and inspect the app.models module and we
    extract all necessary info from it.
    """

    # empty model list
    model_list = []
    # get the models of the app
    app_models = dj_models.get_models(app)
    # remove excluded models
    for item in app_models:
        name = item.__name__
        try:
            exc_list.index(name)
        except ValueError:
            model_list.append(item)

    return model_list


def sort_by_dep(model_list):
    """
    This function sorts a list of models and their dependencies to calculate
    the order in which the models should be loaded by the deserializer
    """

    sorted_list = [ model.__name__ for model in  model_list ]
    deps = []
    for model in model_list:
        if hasattr(model, 'f_dependencies'):
            deps = getattr(model, 'f_dependencies')
            for dep in deps:
                if dep:
                    try:
                        if sorted_list.index(dep) > \
                           sorted_list.index(model.__name__):
                            sorted_list.remove(dep)
                            sorted_list.insert(sorted_list.index(model.__name__), dep)
                    except ValueError:
                        ERRMSG("A model which is a dependency of other"\
                               " objects is not included in the sync. This may"\
                               " cause the sync to fail. Exiting...")
                        gracefull_exit(1)

    return sorted_list


def create_generic_objects(app):
    """
    This function creates a set of generic objects which hold temporary Not Null
    foreign keys for objects which are being installed.
    """

    transaction.commit_unless_managed()
    transaction.enter_transaction_management()
    transaction.managed(True)
#
#    for model in models:
#        mfields = model._meta.fields
#        nn = [ f.name for f in mfields if not f.null and not f.blank ]
#        for field in nn:
#            (type, a, b, c) = model._meta.get_field_by_name(field)
#            if type.__class__.__name__ == 'ForeignKey'\
#                or type.__class__.__name__ == 'OneToOneField':
#                fkey = type.related.parent_model.__name__
#                exec("f_val = Generic"+fkey)
#            else:
#                f_val = 0
#        exec("Generic"+model.__name__+"=models."+model.__name__+"()")
#

    globals()["GenericGarea"] = app.Garea()
    GenericGarea.save()
    globals()["GenericGentity"] = app.Gentity()
    GenericGentity.save()
    globals()["GenericGentityAltCodeType"] = app.GentityAltCodeType()
    GenericGentityAltCodeType.save()
    globals()["GenericGentityAltCode"] = app.GentityAltCode(gentity=GenericGentity, type
            = GenericGentityAltCodeType )
    GenericGentityAltCode.save()
    globals()["GenericFileType"] = app.FileType()
    GenericFileType.save()
    globals()["GenericEventType"] = app.EventType()
    GenericEventType.save()
    globals()["GenericGentityEvent"] = app.GentityEvent(gentity=GenericGentity, type=
                GenericEventType, date = datetime.datetime.now())
    GenericGentityEvent.save()
    #GenericGentityFile = app.GentityFile()

    globals()["GenericGline"] = app.Gline()
    GenericGline.save()

    globals()["GenericGpoint"] = app.Gpoint()
    GenericGpoint.save()
    globals()["GenericInstrumentType"] = app.InstrumentType()
    GenericInstrumentType.save()
    globals()["GenericLentity"] = app.Lentity()
    GenericLentity.save()
    globals()["GenericStation"] = app.Station(owner=GenericLentity)
    GenericStation.save()
    globals()["GenericInstrument"] = app.Instrument(station=GenericStation, type=
                GenericInstrumentType)
    GenericInstrument.save()
    globals()["GenericPerson"] = app.Person()
    GenericPerson.save()
    globals()["GenericVariable"] = app.Variable()
    GenericVariable.save()

    globals()["GenericUnitOfMeasurement"] = app.UnitOfMeasurement()
    GenericUnitOfMeasurement.save()
    globals()["GenericTimeZone"] = app.TimeZone(utc_offset="+2")
    GenericTimeZone.save()

    globals()["GenericTimeStep"] = app.TimeStep(length_minutes=0,
                            length_months=1)
    GenericTimeStep.save()
    globals()["GenericWaterBasin"] = app.WaterBasin()
    GenericWaterBasin.save()
    globals()["GenericWaterDivision"] = app.WaterDivision()
    GenericWaterDivision.save()
    globals()["GenericPoliticalDivision"] = app.PoliticalDivision()
    GenericPoliticalDivision.save()

    transaction.commit()
    transaction.leave_transaction_management()


def store_fkeys(app_name, model_list, object, m2m_keys='None'):
    """
    This function iterates through the fields of the deserialized object and
    finds all foreign keys. After that, by using the original id, he makes sure
    that the foreign keys point to the correct objects.
    """

    foreign_keys = [ f.name for f in object._meta.fields if
                                    isinstance(f, dj_models.ForeignKey) and not
                                    f.name == 'original_db' ]

    if hasattr(object.__class__, 'f_dependencies'):
        deps = getattr(object.__class__, 'f_dependencies')
        parent = deps[0]
    else:
        parent = None

    # get model of parent


    if foreign_keys or m2m_keys:
        try:
            batch_jobs[object.__class__].update( { object.original_id: {
                                        'oid':object.original_id,
                                        'f_keys': {},
                                        'm2m': m2m_keys } })
        except KeyError:
            batch_jobs[object.__class__] = { object.original_id: {
                                        'oid':object.original_id,
                                        'f_keys': {},
                                        'm2m': m2m_keys } }

	# iterate all keys and save them & then make them None
    # keep only inheritance relationship intact
    for key in foreign_keys:
        if parent and key == parent.lower()+'_ptr':
            model = dj_models.get_model(app_name, parent)
            parent_id = getattr(object, key+'_id')
            # get parent object
            po = model.objects.get(original_id=parent_id, original_db=DB)
            # assing new parent pointer
            setattr(object, key, po)
        else:
            key_val = getattr(object, key+'_id')
            if key_val:
                try:
                    fobj = getattr(object, key)
                    go_name = fobj.__class__.__name__
                except:
                    #remote object doesn't exist yet
                    ff = [ f for (f, m) in object._meta.get_fields_with_model()
                                         if f.name == key][0]
                    go_name = ff.related.parent_model.__name__
                # only keep the foreign key if remote object is in the sync
                # list. Otherwise wipe this out.
                if go_name in model_list:
                    batch_jobs[object.__class__][object.original_id]['f_keys'].update({key: key_val})

                try:
                    setattr(object, key, None)
                except ValueError:
                    #Some attributes don't allow Null. Now what?
                    setattr(object, key, eval('Generic'+go_name))


def eval_fkeys(app_name, models):
    """
    This function iterates through all the entries in the ``batch_jobs''
    dictionary and re-evaluates all foreign keys for new objects using the
    original id of the object.
    """

    for model in batch_jobs.keys():
        model_name = model.__name__

        for object_id in batch_jobs[model].keys():
            item = model.objects.get(original_id=str(object_id), original_db=DB)

            # foreign
            if batch_jobs[model][object_id].has_key('f_keys'):
                for (key, val) in batch_jobs[model][object_id]['f_keys'].iteritems():
                    ff = [ f for (f, m) in model._meta.get_fields_with_model() if
                                        f.name==key][0]
                    ro_name = ff.related.parent_model.__name__
                    f_model = dj_models.get_model(app_name, ro_name)
                    setattr(item, key, f_model.objects.get(original_id=val,
                                                            original_db=DB))
            # m2m
            if batch_jobs[model][object_id].has_key('m2m'):
                for (key, vals) in batch_jobs[model][object_id]['m2m'].iteritems():
                    remote_obj = getattr(item, key)
                    remote_class = remote_obj.model.__name__
                    for val in vals:
                        f_model = dj_models.get_model(app_name, remote_class)
                        ro = f_model.objects.get(original_id=val, original_db=DB)
                        m2m_handler = getattr(item, key)
                        if hasattr(m2m_handler, 'add'):
                            m2m_handler.add(ro)
                            # If it doesn't have 'add' it means it is a m2m
                            # with a "through". We don't fix that; instead, we
                            # pray it works.

            item.save()


def MSG(msg, verbose=1):
    """
    STDOUT logging function
    """
    if verbose:
        sys.stdout.write('%s\n' % msg)


def ERRMSG(msg, verbosity=1):
    """
    STDERR logging function
    """
    sys.stderr.write('--> ERROR: %s\n' % msg)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('--remote', '-r', dest='remote',
            help='Remote instance to sync from'),
        make_option('--port', '-p', dest='port',default=80,
            help='Specify custom port. Default is 80.'),
        make_option('--app', '-a', dest='app',
            help='Application which should be synced'),
        make_option('--exclude', '-e', dest='exclude', default=None,
            help='State which models of the apps you want excluded from the'\
                 ' sync'),
        make_option('--fetch-only', '-f', dest='fetch',default=False,
            action='store_true',
            help='Doesn\'t actually submit any changes, just fetches remote'\
                 ' dumps and saves them locally.'),
        make_option('--work-dir', '-w', dest='cwd', default='/tmp',
            help='Define the temp dir in which all temp files will be stored'),
        make_option('--full', '-F', dest='full', default=False,
            action='store_true',
            help='Bypasses last sync date and syncs all of the db again'),
                make_option('--resume', '-R', dest='resume', default=False,
            action='store_true',
            help='With resume, no files are fetched but the local ones are used'),
        make_option('--silent', '-S', dest='verbose', default=True,
            action='store_false',
            help='Suppress all log messages',)
    )
    help = 'This command is used to synchronize the local database using data'\
           ' from a remote instance'

    def handle(self, *args, **options):

        # Get a cursor and init the db
        cursor = connection.cursor()

        # keep record of installed stuff
        inst_models = set()
        fixture_count = 0
        object_count = 0

        # Save command line opts
        remote = options.get('remote', None)
        port = options.get('port')
        app_name = options.get('app', None)
        exclude = options.get('exclude', None)
        pretend = options.get('pretend')
        ask = options.get('ask')
        interactive = options.get('interactive')
        clean = options.get('clean')
        full = options.get('full')
        no_backup = options.get('bkp')
        verbose = options.get('verbose')
        fetch = options.get('fetch')
        resume = options.get('resume')
        cwd = options.get('cwd')

        # check if we have a remote node and an app
        if not remote or not app_name:
            ERRMSG('You must specify at least one remote system and app to'\
                   ' sync')
            sys.exit(1)

        # handle silent option
        if not verbose:
            null = file("/dev/null", "a")
            sys.stdout = sys.stderr = null

        # Check if remote node is listening
        if check_remote(remote, port):
            MSG('Remote host is up. Continuing with the sync.')
        else:
            ERRMSG('Connection error. Make sure the remote application is'\
                   ' running and that you specified the correct connection'\
                   ' parameters.')
            sys.exit(1)

        # check if remote instance is in Databases
        try:
            globals()["DB"] = Database.objects.get(hostname__contains=remote)
        except Exception:
            ERRMSG('The remote host you have provided is not in the database'\
                   ' table of our application. Please insert the host via the'\
                   ' admin panel and then try again.')
            gracefull_exit(1)

        # import the app's models
        try:
            app = get_app(app_name)
        except ImproperlyConfigured:
            ERRMSG('Could not load application %s. Exiting...' % app)
            sys.exit(1)

        if exclude:
            exc_list = exclude.split(',')
        else:
            exc_list = []


        # try to get a model list
        try:
            models = get_models(app, exc_list)
        except:
            ERRMSG('Could not get a list of models inside the specified app.'\
                   ' This should not happen...')
            sys.exit(1)

        # exclude specified models
        MSG("The following models will be synced: %s" %
                [m.__name__ for m in models] )
        if exclude:
            MSG("The following models will be excluded %s" %
                [m for m in exc_list] )

        # change cwd
        try:
            os.chdir(cwd)
        except OSError:
            ERR_MSG("Could not chdir to %s. You could provide another custon"\
                    " temp directory using the -w switch." % cwd)

        # get the sync timestamp
        sync_timestamp = datetime.datetime.now()

        if not resume:
            # Get the fixture for each model
            for model in models:
                MSG("Syncing model %s" % model.__name__)
                request_url = ('http://%s:%s/api/%s/' %
                                 (remote, str(port),model.__name__))
                try:
                    if DB.last_sync and not full:
                        timestamp = urlquote(str(DB.last_sync))
                        req = urllib2.Request("%smodified_after/%s/" % (request_url,
                                                                        timestamp))
                    else:
                        req = urllib2.Request(request_url)

                    with RotatingThing(" - Downloading %s fixtures  " % \
                                                model.__name__):
                        response = urllib2.urlopen(req)
                except Exception, detail:
                    ERRMSG("Error fetching fixtures. %s" % detail)

                j = self.backward_api(response, app_name, model)

                # and save it to a local file
                try:
                    local_file = open(model.__name__+'.json', "w")
                    json.dump(j, local_file)
                    local_file.close()
                except:
                    ERRMSG('Error saving local file %s. Check cwd permissions and'\
                           ' try again.' %model.__name__+'.json')

            # If fetch-only run was specified, exit now
            if fetch:
                MSG("\nFinished fetching files. Exiting now...")
                gracefull_exit(0)

        # Create Generic objects to handle temporary dependencies
        MSG("Creating Generic objects")
        create_generic_objects(app)
        MSG("Finished with Generic objects")

        # transaction management
        transaction.commit_unless_managed()
        transaction.enter_transaction_management()
        transaction.managed(True)

        # sort models by dependencies so that deps will be loaded first
        models = sort_by_dep(models)

        # Open the files on by one and load the fixtures in the db
        for model in models:
            try:
                fd = file(model+'.json', 'r')
            except IOError:
                ERRMSG("Error opening file %s." % (model+'.json'))
                gracefull_exit(1)

            MSG("Installing fixtures from file %s.json" % model)

            # do the object deserialization
            try:
                objects = serializers.deserialize('json', fd)
            except:
                ERRMSG("Error deserializing objects for class %s." % \
                        model)
                objects = None
                gracefull_exit(1)

            # handle each deserialized object
            for obj in objects:
                inst_models.add(obj.object.__class__)

                try:
                    obj_type = dj_models.get_model(app_name, obj.object.__class__.__name__)
                    upd_obj = obj_type.objects.get(original_id=obj.object.pk, original_db=DB)
                except Exception, detail:
                    # not already in db
                    obj.object.original_id = obj.object.pk
                    obj.object.id = None
                else:
                    # object in db. updating...
                    obj.object.id = upd_obj.id
                    obj.object.original_id = upd_obj.original_id

                # Here we must also populate the additional fields and
                # check every addition against the existing objects!
                store_fkeys(app_name, models, obj.object, obj.m2m_data)

                obj.m2m_data = {}
                obj.object.original_db = DB

                try :
                    obj.save()
                    object_count += 1
                except Exception, details:
                    ERRMSG("Error saving an object of type %s\n%s" %\
                            (model, details) )
                    transaction.rollback()
                    transaction.leave_transaction_management()
                    gracefull_exit(1)


            fd.close()
            os.unlink(fd.name)
            fixture_count += 1

        try:
            with RotatingThing("Reinitializing foreign keys:  "):
                eval_fkeys(app_name, models)
        except Exception, details:
            ERRMSG("Error setting up foreign keys: %s" % details)
            transaction.rollback()
            transaction.leave_transaction_management()
            gracefull_exit(1)

        # transaction end
        transaction.commit()
        transaction.leave_transaction_management()

        MSG("Successfully installed %d objects from %d fixtures." %
                (object_count, fixture_count) )

        # close connection
        connection.close()

        # update DB last sync timestamp
        setattr(DB, 'last_sync', sync_timestamp)
        DB.save()

        # wrap-up and exit
        gracefull_exit(0)

    def backward_api(self, response, app_name, model):
        """
        The dbsync application was originally written for some kind of
        webservice API we had then. Either that API was compatible
        with the Django deserializer, or I don't understand something
        (or both).  The API since has changed. So here we hackily
        convert the results given by the new API so that it's like the
        results of the old API.  In the old API, each item had a "pk",
        a "model", and a "fields" dictionary with all the other
        fields. In the new API, there is an "id", there is no "model"
        (we know which model it is), and all the other fields are
        there, siblings of "id" (not nested inside a "fields"
        dictionary).

        If results are already in the old API, we don't touch it.
        """
        result = []
        try:
            j = json.load(response)
        except ValueError:
            return result
        if len(j) < 1:
            return result
        if ('pk' in j[0]) and ('model' in j[0]) and ('fields' in j[0]) and (
                'id' not in j[0]):
            # Old API: return as is
            result = j
            return result
        for x in j:
            item = {
                'pk': x['id'],
                'model': app_name + '.' + model.__name__,
                'fields': {},
            }
            for k in x:
                if x == 'id':
                    continue
                item['fields'][k] = x[k]
            result.append(item)
        return result

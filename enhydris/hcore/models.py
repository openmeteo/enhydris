from django.db import connection as db_connection
from django.conf import settings
from django.contrib.gis.db import models
from django.contrib.gis.db.backends import postgis
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_syncdb, post_save
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.db.models import signals
from pthelma import timeseries
from enhydris.hcore.utils import *

# Lookups
class Lookup(models.Model):
    last_modified = models.DateTimeField(default=timezone.now, null=True, editable=False)

    descr = models.CharField(max_length=200, blank=True)
    descr_alt = models.CharField(max_length=200, blank=True)
    class Meta:
        abstract = True
        ordering = ('descr',)

    def __unicode__(self):
        return self.descr or self.descr_alt

# Lentity and descendants
def post_save_person_or_organization(sender, **kwargs):
    instance = kwargs['instance']
    try:
        string = instance.name
    except:
        string = instance.last_name + instance.first_name
    lentity = instance.lentity_ptr
    lentity.ordering_string = string
    super(Lentity, lentity).save()


class Lentity(models.Model):
    last_modified = models.DateTimeField(default=timezone.now, null=True, editable=False)

    remarks = models.TextField(blank=True)
    remarks_alt = models.TextField(blank=True)
    ordering_string = models.CharField(max_length=255, null=True,
                        blank=True,editable=False)

    class Meta:
        verbose_name_plural="Lentities"
        ordering = ('ordering_string',)
    def __unicode__(self):
        return (self.remarks or self.remarks_alt or self.name_any or str(self.id))

    @property
    def name_any(self):
        len_name = ""
        try:
            lentity = Person.objects.get(pk=self.id)
            len_name = lentity.last_name+" "+lentity.first_name
        except Person.DoesNotExist:
            try:
                lentity = Organization.objects.get(pk=self.id)
                len_name = lentity.name
            except Organization.DoesNotExist:
                pass

        return len_name

class Person(Lentity):
    last_name = models.CharField(max_length=100, blank=True)
    first_name = models.CharField(max_length=100, blank=True)
    middle_names = models.CharField(max_length=100, blank=True)
    initials = models.CharField(max_length=20, blank=True)
    last_name_alt = models.CharField(max_length=100, blank=True)
    first_name_alt = models.CharField(max_length=100, blank=True)
    middle_names_alt = models.CharField(max_length=100, blank=True)
    initials_alt = models.CharField(max_length=20, blank=True)
    f_dependencies = ['Lentity']
    class Meta:
        ordering = ('last_name', 'first_name',)
    def __unicode__(self):
        return self.last_name + ' ' + self.initials

post_save.connect(post_save_person_or_organization, sender=Person)

class Organization(Lentity):
    name = models.CharField(max_length=200, blank=True)
    acronym = models.CharField(max_length=50, blank=True)
    name_alt = models.CharField(max_length=200, blank=True)
    acronym_alt = models.CharField(max_length=50, blank=True)
    f_dependencies = ['Lentity']

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return self.acronym if self.acronym else self.name

post_save.connect(post_save_person_or_organization, sender=Organization)

# Gentity and direct descendants
class Gentity(models.Model):
    last_modified = models.DateTimeField(default=timezone.now, null=True, editable=False)

    water_basin = models.ForeignKey('WaterBasin', null=True, blank=True)
    water_division = models.ForeignKey('WaterDivision', null=True, blank=True)
    political_division = models.ForeignKey('PoliticalDivision',
                                                null=True, blank=True)
    name = models.CharField(max_length=200, blank=True)
    short_name = models.CharField(max_length=50, blank=True)
    remarks = models.TextField(blank=True)
    name_alt = models.CharField(max_length=200, blank=True)
    short_name_alt = models.CharField(max_length=50, blank=True)
    remarks_alt = models.TextField(blank=True)
    class Meta:
        verbose_name_plural="Gentities"
        ordering = ('name',)
    def __unicode__(self):
        return self.short_name or self.short_name_alt or self.name \
            or self.name_alt or str(self.id)

class Gpoint(Gentity):
    srid = models.IntegerField(null=True, blank=True)
    approximate = models.BooleanField(default=False)
    altitude = models.FloatField(null=True, blank=True)
    asrid = models.IntegerField(null=True, blank=True)
    f_dependencies = ['Gentity']
    point = models.PointField(null=True, blank=True)
    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        super(Gpoint, self).save(force_insert, force_update, *args, **kwargs)
    def original_abscissa(self):
        if self.point:
            (x, y) = self.point.transform(self.srid, clone=True)
            return round(x, 2) if abs(x)>180 and abs(y)>90 else x
        else:
            return None
    def original_ordinate(self):
        if self.point:
            (x, y) = self.point.transform(self.srid, clone=True)
            return round(y, 2) if abs(x)>180 and abs(y)>90 else y
        else:
            return None
    def original_cs_name(self):
        if self.srid:
            srtext = postgis.models.PostGISSpatialRefSys.objects.get(
                srid=self.srid).srtext
            cstype, dummy, rest = srtext.partition('[')
            csname = rest.split('"')[1]
            return csname + ' (' + cstype + ')'


class Gline(Gentity):
    gpoint1 = models.ForeignKey(Gpoint, null=True, blank=True, related_name='glines1')
    gpoint2 = models.ForeignKey(Gpoint, null=True, blank=True, related_name='glines2')
    length = models.FloatField(null=True, blank=True)
    f_dependecies = ['Gentity']
    linestring = models.LineStringField(null=True, blank=True)

class Garea(Gentity):
    area = models.FloatField(null=True, blank=True)
    f_dependencies = ['Gentity']
    mpoly = models.MultiPolygonField(null=True, blank=True)
    def __unicode__(self):
        if self.area: return str(self.id)+" ("+str(self.area)+")"
        return str(self.id)

# Gentity-related models
class PoliticalDivisionManager(models.Manager):
    """This is the default model Manager enhanced with utility methods."""

    def get_leaf_subdivisions(self, local_parent):
        """Gets a parent PoliticalDivision and returns all its tree leaves.

        Leaves are the last political division level elements. The method
        iterates on every node of the parent subtree and returns only the
        bottom level elements.
        CAUTION! This returns a "list" not a "QuerySet"!!!
        """

        child = None
        children = []
        object =  PoliticalDivision.objects.get(pk=local_parent)
        parents = PoliticalDivision.objects.all().filter(
                            Q(name=object.name)&
                            Q(short_name=object.short_name)&
                            Q(name_alt=object.name_alt)&
                            Q(short_name_alt=object.short_name_alt))
        for parent in parents:
            children.append(parent)
            for child in self.filter(parent=parent.id):
                try:
                    children.extend(self.get_leaf_subdivisions(child.id))
                except TypeError:
                    # This is the case we have only an object instance, not a list
                    children.append(self.get_leaf_subdivisions(child.id))

        if children:
            return children
        if not child:
            return [ p for p in parents ]

class PoliticalDivision(Garea):
    parent = models.ForeignKey('self', null=True, blank=True)
    code = models.CharField(max_length=5, blank=True)

    # Managers
    objects = PoliticalDivisionManager()

    f_dependencies = ['Garea']
    def __unicode__(self):
        result = self.short_name or self.name or self.short_name_alt \
            or self.name_alt or str(self.id)
        if self.parent: result = result + ', ' + self.parent.__unicode__()
        return result

class WaterDivision(Garea):
    # TODO: Fill in the model
    f_dependencies = ['Garea']
    def __unicode__(self):
        return self.name or str(self.id)

class WaterBasin(Garea):
    parent = models.ForeignKey('self', null=True, blank=True)
    f_dependencies = ['Garea']
    def __unicode__(self):
        return self.name or str(self.id)


class GentityAltCodeType(Lookup): pass

class GentityAltCode(models.Model):
    last_modified = models.DateTimeField(default=timezone.now, null=True, editable=False)

    gentity = models.ForeignKey(Gentity)
    type = models.ForeignKey(GentityAltCodeType)
    value = models.CharField(max_length=100)
    def __unicode__(self):
        return self.type.descr+' '+self.value
    @property
    def related_station(self):
        try:
            return Station.objects.get(id=self.gentity.id)
        except:
            return None

class GentityGenericDataType(Lookup):
    file_extension = models.CharField(max_length=16)

class GentityGenericData(models.Model):
    last_modified = models.DateTimeField(default=timezone.now, null=True, editable=False)

    gentity = models.ForeignKey(Gentity)
    descr = models.CharField(max_length=100)
    remarks = models.TextField(blank=True)
    descr_alt = models.CharField(max_length=100)
    remarks_alt = models.TextField(blank=True)
    content = models.TextField(blank=True)
    data_type = models.ForeignKey(GentityGenericDataType)
    def __unicode__(self):
        return self.descr or self.descr_alt or str(self.id)
    @property
    def related_station(self):
        try:
            return Station.objects.get(id=self.gentity.id)
        except:
            return None

class FileType(Lookup):
    mime_type = models.CharField(max_length=64)
    def __unicode__(self):
        if self.mime_type: return self.mime_type
        return str(self.id)

class GentityFile(models.Model):
    last_modified = models.DateTimeField(default=timezone.now, null=True, editable=False)

    gentity = models.ForeignKey(Gentity)
    date = models.DateField(blank=True, null=True)
    file_type = models.ForeignKey(FileType)
    content = models.FileField(upload_to='gentityfile')
    descr = models.CharField(max_length=100)
    remarks = models.TextField(blank=True)
    descr_alt = models.CharField(max_length=100)
    remarks_alt = models.TextField(blank=True)
    def __unicode__(self):
        return self.descr or self.descr_alt or str(self.id)
    @property
    def related_station(self):
        try:
            return Station.objects.get(id=self.gentity.id)
        except:
            return None

class EventType(Lookup): pass

class GentityEvent(models.Model):
    last_modified = models.DateTimeField(default=timezone.now, null=True, editable=False)

    gentity = models.ForeignKey(Gentity)
    date = models.DateField()
    type = models.ForeignKey(EventType)
    user = models.CharField(max_length=64)
    report = models.TextField(blank=True)
    report_alt = models.TextField(blank=True)
    class Meta:
        ordering = ['-date']
    def __unicode__(self):
        return str(self.date)+' '+self.type.__unicode__()
    @property
    def related_station(self):
        try:
            return Station.objects.get(id=self.gentity.id)
        except:
            return None

# Station and its related models
class StationType(Lookup): pass

class StationManager(models.GeoManager):
    """Default manager enhanced with utility methods."""

    def get_by_political_division(self, political_division):
        """Get all stations which belong to the specific political division."""
        leaves = PoliticalDivision.objects.get_leaf_subdivisions(political_division)
        return Station.objects.filter(political_division__in=leaves)

def handle_maintainer_permissions(sender, instance, **kwargs):
    from enhydris.permissions.models import Permission
    from django.contrib.contenttypes.models import ContentType


    if settings.ENHYDRIS_USERS_CAN_ADD_CONTENT:
        old_perms = Permission.objects.filter(
                        object_id=instance.pk,
                        content_type=ContentType.objects.get_for_model(Station))

        old_users = [ p.user for p in old_perms ]
        new_users = instance.maintainers.all()
        # remove all old perms for maintainers. keep for creator
        for p in old_perms:
            if not p.user == instance.creator:
                p.delete()

        # add new perms
        [ u.add_row_perm(instance,'edit') for u in new_users ]
    else:
        pass

class Station(Gpoint):
    owner = models.ForeignKey(Lentity, related_name="owned_stations")
    stype = models.ManyToManyField(StationType, verbose_name='type')
    is_automatic = models.BooleanField(default=False)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    overseers = models.ManyToManyField(Person, through='Overseer',
                                    related_name='stations_overseen')
    copyright_holder = models.TextField()
    copyright_years = models.CharField(max_length=10)
    # The following two fields are only useful when USERS_CAN_ADD_CONTENT
    # is set.
    creator = models.ForeignKey(User, null=True, blank=True,
                     related_name='created_stations')
    maintainers = models.ManyToManyField(User, blank=True,
                                         related_name='maintaining_stations')


    f_dependencies = ['Gpoint']
    # Managers
    objects = StationManager()

    def show_overseers(self):
        return " ".join([i.__unicode__() for i in self.overseers.all()])
    show_overseers.short_description = "List of Overseers"

signals.post_save.connect(handle_maintainer_permissions, Station)

class Overseer(models.Model):
    last_modified = models.DateTimeField(default=timezone.now, null=True, editable=False)

    station = models.ForeignKey(Station)
    person = models.ForeignKey(Person)
    is_current = models.BooleanField(default=False)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    def __unicode__(self):
        return self.person.__unicode__()

class InstrumentType(Lookup): pass

class Instrument(models.Model):

    class Meta:
        ordering = ('name',)

    last_modified = models.DateTimeField(default=timezone.now, null=True, editable=False)

    station = models.ForeignKey(Station)
    type = models.ForeignKey(InstrumentType)
    manufacturer = models.CharField(max_length=50, blank=True)
    model = models.CharField(max_length=50, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    name = models.CharField(max_length=100, blank=True)
    remarks = models.TextField(blank=True)
    name_alt = models.CharField(max_length=100, blank=True)
    remarks_alt = models.TextField(blank=True)
    def __unicode__(self):
        # This gets commended out because it causes significant delays #XXX:
        #return self.name or self.name_alt or self.type.descr or str(self.id)
        return self.name or str(self.id)


# Time series and related models
class Variable(Lookup): pass

class UnitOfMeasurement(Lookup):
    symbol = models.CharField(max_length=50)
    variables = models.ManyToManyField(Variable)
    def __unicode__(self):
        if self.symbol: return self.symbol
        return str(self.id)

class TimeZone(models.Model):
    last_modified = models.DateTimeField(default=timezone.now, null=True, editable=False)

    code = models.CharField(max_length=50)
    utc_offset = models.SmallIntegerField()
    def __unicode__(self):
        return '%s (UTC%+03d%02d)' % (self.code,
                (abs(self.utc_offset) / 60)* (-1 if self.utc_offset<0 else 1), 
                abs(self.utc_offset % 60),)
    class Meta:
        ordering = ('utc_offset',)

def _int_xor(i1, i2):
    """Return True if one and only one of i1 and i2 is zero."""
    return (i1 or i2) and not (i1 and i2)

class TimeStep(Lookup):
    length_minutes = models.PositiveIntegerField()
    length_months = models.PositiveSmallIntegerField()
    def __unicode__(self):
        """
        Return timestep descriptions in a more human readable format
        """
        days = self.length_minutes / 1440
        hours = self.length_minutes / 60 - 24 * days
        minutes = self.length_minutes - 60 * hours - 1440 * days
        years = self.length_months / 12
        months = self.length_months - years*12
        if self.descr<>"":
            desc = self.descr+" - "
        else:
            desc = ""
        link = ""
        if years:
            desc += "%d year(s)" % years
            link = ','
        if months:
            desc += link+"%d month(s)" % months
            link = ','
        if days:
            desc += link+"%d day(s)" % days
            link = ','
        if hours:
            desc += link+"%d hour(s)" % hours
            link = ','
        if minutes:
            desc += link+"%d minute(s)" % minutes
            link = ','
        if desc:
            return desc
        return "(0,0)"
    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        if not _int_xor(self.length_minutes, self.length_months):
            raise Exception(_("%s is not a valid time step; exactly one of minutes and months must be zero") % self.__unicode__())
        super(TimeStep, self).save(force_insert, force_update, *args, **kwargs)

class IntervalType(Lookup):
    value = models.CharField(max_length=50)
    def __unicode__(self):
        return self.descr

class Timeseries(models.Model):
    last_modified = models.DateTimeField(default=timezone.now, null=True, editable=False)

    gentity = models.ForeignKey(Gentity, related_name="timeseries")
    variable = models.ForeignKey(Variable)
    unit_of_measurement = models.ForeignKey(UnitOfMeasurement)
    name = models.CharField(max_length=200, blank=True)
    name_alt = models.CharField(max_length=200, blank=True, default='')
    hidden = models.BooleanField(null=False, blank=False, default=False)
    precision = models.SmallIntegerField(null=True, blank=True)
    time_zone = models.ForeignKey(TimeZone)
    remarks = models.TextField(blank=True)
    remarks_alt = models.TextField(blank=True, default='')
    instrument = models.ForeignKey(Instrument, null=True, blank=True)
    time_step = models.ForeignKey(TimeStep, null=True, blank=True)
    interval_type = models.ForeignKey(IntervalType, null=True, blank=True)
    timestamp_rounding_minutes = models.PositiveIntegerField(null=True,
                                                             blank=True)
    timestamp_rounding_months = models.PositiveSmallIntegerField(null=True,
                                                                 blank=True)
    timestamp_offset_minutes = models.IntegerField(null=True, blank=True)
    timestamp_offset_months = models.SmallIntegerField(null=True, blank=True)
    class Meta:
        verbose_name = "Time Series"
        verbose_name_plural = "Time Series"
        ordering = ('hidden',)
    @property
    def start_date(self):
        try:
            ts = timeseries.Timeseries(int(self.id))
        except:
            return None
        # This should be removed if ticket #112 gets resolved
        c = db_connection.cursor()
        c.execute("SELECT timeseries_start_date(%s)", (ts.id,))
        try:
            r = c.fetchone()
        except:
            return None

        c.close()
        return r[0]
    @property
    def end_date(self):
        try:
            ts = timeseries.Timeseries(int(self.id))
        except:
            return None
        # This should be removed if ticket #112 gets resolved
        c = db_connection.cursor()
        c.execute("SELECT timeseries_end_date(%s)", (ts.id,))
        try:
            r = c.fetchone()
        except:
            return None

        c.close()
        return r[0]
    @property
    def related_station(self):
        try:
            return Station.objects.get(id=self.gentity.id)
        except:
            return None
    def __unicode__(self):
        return self.name
    def save(self, force_insert=False, force_update=False, *args, **kwargs):
        if not self.time_step:
            if self.timestamp_rounding_minutes or self.timestamp_rounding_months \
            or self.timestamp_offset_minutes or self.timestamp_offset_months:
                raise Exception(_("Invalid time step: if time_step is null, rounding and offset must also be null"))
        else:
            if self.timestamp_offset_minutes is None \
            or self.timestamp_offset_months is None:
                raise Exception(_("Invalid time step: if time_step is not null, offset must be provided"))
            if (self.timestamp_rounding_minutes is None
                                and self.timestamp_rounding_months is not None) \
                        or (self.timestamp_rounding_minutes is not None
                                    and self.timestamp_rounding_months is None):
                raise Exception(_("Invalid time step: roundings must be both null or not null"))
        super(Timeseries, self).save(force_insert, force_update, *args, **kwargs)


# The ts_records table was never intended to be a Django model; in fact it was
# originally created by plain SQL; however, this caused some problems (see
# ticket #245), and therefore it was changed to be a Django model. However, it
# should not be used as a Django model; it should be manipulated through
# pthelma.timeseries.Timeseries methods read_from_db(), write_to_db(), and
# append_to_db(). (Besides, in the future the internal are very likely to
# change, and the ts_records table is likely to be removed, and instead there
# will be a FileField in the Timeseries model.)

class BlobField(models.Field):
    def db_type(self, connection):
        return 'bytea'


# The following two lines were needed when we were using South. It's not clear
# to me that Django>=1.7 doesn't need anything like that. If some time goes by
# and some migrations are made and everything works fine, remove. 2015-06-25
#
# from south.modelsinspector import add_introspection_rules
# add_introspection_rules([], ["^enhydris\.hcore\.models\.BlobField"])


class TsRecords(models.Model):
    id = models.OneToOneField(Timeseries, primary_key=True, db_column='id')
    top = models.TextField(blank=True)
    middle = BlobField(null=True, blank=True)
    bottom = models.TextField()
    class Meta:
        db_table = 'ts_records'


# Profile creation upon user registration
def user_post_save(sender, instance, **kwargs):
    profile, new = UserProfile.objects.get_or_create(user=instance)

def make_user_editor(sender, instance, **kwargs):
    user = instance
    if not user.is_superuser:
        group, created = Group.objects.get_or_create(name='editors')
        user.groups.add(group)

#Read time step from Timeseries Object
from pthelma.timeseries import TimeStep as TTimeStep
from pthelma.timeseries import IntervalType as it

def ReadTimeStep(id, timeseries_instance = None):
    if timeseries_instance == None:
        from django.shortcuts import get_object_or_404
        timeseries_instance = get_object_or_404(Timeseries, pk=int(id))
    t = timeseries_instance
    return TTimeStep(
        length_minutes = t.time_step.length_minutes if t.time_step
                                    else 0,
        length_months = t.time_step.length_months if t.time_step
                                    else 0,
        timestamp_rounding = None if None in
                    (t.timestamp_rounding_minutes, t.timestamp_rounding_months)
               else (t.timestamp_rounding_minutes, t.timestamp_rounding_months),
        timestamp_offset = None if None in
                    (t.timestamp_offset_minutes, t.timestamp_offset_months)
               else (t.timestamp_offset_minutes, t.timestamp_offset_months),
        interval_type = None if not t.interval_type else\
                {'sum': it.SUM, 'average': it.AVERAGE,\
                 'vector_average': it.VECTOR_AVERAGE,\
                 'minimum': it.MINIMUM,\
                 'maximum': it.MAXIMUM}[t.interval_type.value.lower()])


# Class for user profiles
class UserProfile(models.Model):
    user = models.OneToOneField(User, verbose_name=_('Username'))
    fname = models.CharField(_('First Name'),null=True,blank=True, max_length=30)
    lname = models.CharField(_('Last Name'),null=True,blank=True, max_length=30)
    address = models.CharField(_('Location'),null=True,blank=True,max_length=100)
    organization = models.CharField(_('Organization'),null=True,blank=True,max_length=100)
    email_is_public = models.BooleanField(default=False)

    def __unicode__(self):
        name = self.user.get_full_name()
        if name:
            return unicode("%s" % self.user.get_full_name())
        else:
            return unicode("%s" % self.user.username)

    class Meta:
        verbose_name = _('Profile')
        verbose_name_plural = _('Profiles')

    def first_name(self):
        return u"%s" % self.fname

    def last_name(self):
        return u"%s" % self.lname

    def full_name(self):
        if self.fname == self.lname == None\
           or self.fname == self.lname == '':
            return "No name specified"
        return u"%s %s" % (self.fname, self.lname)

    def email(self):
        return u"%s" % self.user.email

signals.post_save.connect(user_post_save, User)

if settings.ENHYDRIS_USERS_CAN_ADD_CONTENT:
    signals.post_save.connect(make_user_editor, User)


import enhydris.hcore.signals
post_syncdb.connect(enhydris.hcore.signals.after_syncdb)

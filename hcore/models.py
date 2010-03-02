from django.db import connection as db_connection
from django.db import models
from django.contrib.auth.models import User, Group
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.db.models import signals
from pthelma import timeseries
from enhydris.hcore.utils import *
from enhydris.dbsync.models import Database

# Lookups
class Lookup(models.Model):
    # for db sync issues
    original_id = models.IntegerField(null=True, blank=True, editable=False)
    original_db = models.ForeignKey(Database, null=True, editable=False)
    last_modified = models.DateTimeField(auto_now=True, null=True, editable=False)

    descr = models.CharField(max_length=200, blank=True)
    descr_alt = models.CharField(max_length=200, blank=True)
    class Meta:
        abstract = True
    def __unicode__(self):
        return self.descr or self.descr_alt

# Lentity and descendants
class Lentity(models.Model):
    # for db sync issues
    original_id = models.IntegerField(null=True, blank=True, editable=False)
    original_db = models.ForeignKey(Database, null=True, editable=False)
    last_modified = models.DateTimeField(auto_now=True, null=True, editable=False)

    remarks = models.TextField(blank=True)
    remarks_alt = models.TextField(blank=True)
    class Meta:
        verbose_name_plural="Lentities"
    def __unicode__(self):
        return (self.remarks or self.remarks_alt or self.name_any or str(self.id))

    @property
    def name_any(self):
        len_name = ""
        try:
            lentity = Person.objects.get(pk=self.id)
            len_name = lentity.first_name+" "+lentity.last_name
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
    def __unicode__(self):
        return self.last_name + ' ' + self.initials

class Organization(Lentity):
    name = models.CharField(max_length=200, blank=True)
    acronym = models.CharField(max_length=50, blank=True)
    name_alt = models.CharField(max_length=200, blank=True)
    acronym_alt = models.CharField(max_length=50, blank=True)
    f_dependencies = ['Lentity']
    def __unicode__(self):
        if self.acronym: return self.acronym
        return str(self.id)

# Gentity and direct descendants
class Gentity(models.Model):
    # for db sync issues
    original_id = models.IntegerField(null=True, blank=True, editable=False)
    original_db = models.ForeignKey(Database, null=True, editable=False)
    last_modified = models.DateTimeField(auto_now=True, null=True, editable=False)

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
    def __unicode__(self):
        return self.short_name or self.short_name_alt or self.name \
            or self.name_alt or str(self.id)

class Gpoint(Gentity):
    abscissa = models.FloatField(null=True, blank=True)
    ordinate = models.FloatField(null=True, blank=True)
    srid = models.IntegerField(null=True, blank=True)
    approximate = models.BooleanField()
    altitude = models.FloatField(null=True, blank=True)
    asrid = models.IntegerField(null=True, blank=True)
    f_dependencies = ['Gentity']
    def save(self, force_insert=False, force_update=False):
        super(Gpoint, self).save(force_insert, force_update)

class Gline(Gentity):
    gpoint1 = models.ForeignKey(Gpoint, null=True, blank=True, related_name='glines1')
    gpoint2 = models.ForeignKey(Gpoint, null=True, blank=True, related_name='glines2')
    length = models.FloatField(null=True, blank=True)
    f_dependecies = ['Gentity']

class Garea(Gentity):
    area = models.FloatField(null=True, blank=True)
    f_dependencies = ['Gentity']
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
        for child in self.filter(parent=local_parent):
            try:
                children.extend(self.get_leaf_subdivisions(child))
            except TypeError:
                # This is the case we have only an object instance, not a list
                children.append(self.get_leaf_subdivisions(child))
        if children:
            return children
        if not child:
            return [ local_parent ]

class PoliticalDivision(Garea):
    parent = models.ForeignKey('self', null=True, blank=True)
    code = models.CharField(max_length=5, blank=True)

    # Managers
    objects = PoliticalDivisionManager()

    f_dependencies = ['Garea']
    def __unicode__(self):
        result = self.short_name or self.name or self.short_name_alt \
            or self.name_alt or self.id
        if self.parent: result = result + ', ' + self.parent.__unicode__()
        return result

class WaterDivision(Garea):
    # TODO: Fill in the model
    f_dependencies = ['Garea']
    def __unicode__(self):
        return self.name or str(self.id)

class WaterBasin(Garea):
    parent = models.ForeignKey('self', null=True, blank=True)
    water_division = models.ForeignKey(WaterDivision, null=True, blank=True)
    f_dependencies = ['Garea']
    def __unicode__(self):
        return self.name or str(self.id)


class GentityAltCodeType(Lookup): pass

class GentityAltCode(models.Model):
    # for db sync issues
    original_id = models.IntegerField(null=True, blank=True, editable=False)
    original_db = models.ForeignKey(Database, null=True, editable=False)
    last_modified = models.DateTimeField(auto_now=True, null=True, editable=False)

    gentity = models.ForeignKey(Gentity)
    type = models.ForeignKey(GentityAltCodeType)
    value = models.CharField(max_length=100)
    def __unicode__(self):
        return self.type.descr+' '+self.type.value

class FileType(Lookup):
    mime_type = models.CharField(max_length=64)
    def __unicode__(self):
        if self.mime_type: return self.mime_type
        return str(self.id)

class GentityFile(models.Model):
    # for db sync issues
    original_id = models.IntegerField(null=True, blank=True, editable=False)
    original_db = models.ForeignKey(Database, null=True, editable=False)
    last_modified = models.DateTimeField(auto_now=True, null=True, editable=False)


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

class EventType(Lookup): pass

class GentityEvent(models.Model):
    # for db sync issues
    original_id = models.IntegerField(null=True, blank=True, editable=False)
    original_db = models.ForeignKey(Database, null=True, editable=False)
    last_modified = models.DateTimeField(auto_now=True, null=True, editable=False)

    gentity = models.ForeignKey(Gentity)
    date = models.DateField()
    type = models.ForeignKey(EventType)
    user = models.CharField(max_length=64)
    report = models.TextField(blank=True)
    report_alt = models.TextField(blank=True)
    def __unicode__(self):
        return str(self.date)+' '+self.type.__unicode__()

# Station and its related models

class StationType(Lookup): pass

class StationManager(models.Manager):
    """Default manager enhanced with utility methods."""

    def get_by_political_division(self, political_division):
        """Get all stations which belong to the specific political division."""
        leaves = PoliticalDivision.objects.get_leaf_subdivisions(political_division)
        return Station.objects.filter(political_division__in=leaves)


class Station(Gpoint):
    owner = models.ForeignKey(Lentity)
    type = models.ForeignKey(StationType)
    is_automatic = models.BooleanField()
    is_active = models.BooleanField()
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    overseers = models.ManyToManyField(Person, through='Overseer',
                                    related_name='stations_overseen')
    if hasattr(settings, 'USERS_CAN_ADD_CONTENT')\
        and settings.USERS_CAN_ADD_CONTENT:
            creator = models.ForeignKey(User, null=True, blank=True,
                     related_name='created_stations')
            maintainers = models.ManyToManyField(User,
                     related_name='maintaining_stations', null=True,blank=True)


    f_dependencies = ['Gpoint']
    # Managers
    objects = StationManager()

    def show_overseers(self):
        return " ".join([i.__unicode__() for i in self.overseers.all()])
    show_overseers.short_description = "List of Overseers"

class Overseer(models.Model):
    # for db sync issues
    original_id = models.IntegerField(null=True, blank=True, editable=False)
    original_db = models.ForeignKey(Database, null=True, editable=False)
    last_modified = models.DateTimeField(auto_now=True, null=True, editable=False)

    station = models.ForeignKey(Station)
    person = models.ForeignKey(Person)
    is_current = models.BooleanField()
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    def __unicode__(self):
        return self.person.__unicode__()

class InstrumentType(Lookup): pass

class Instrument(models.Model):
    # for db sync issues
    original_id = models.IntegerField(null=True, blank=True, editable=False)
    original_db = models.ForeignKey(Database, null=True, editable=False)
    last_modified = models.DateTimeField(auto_now=True, null=True, editable=False)

    station = models.ForeignKey(Station)
    type = models.ForeignKey(InstrumentType)
    manufacturer = models.CharField(max_length=50, blank=True)
    model = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField()
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
    # for db sync issues
    original_id = models.IntegerField(null=True, blank=True, editable=False)
    original_db = models.ForeignKey(Database, null=True, editable=False)
    last_modified = models.DateTimeField(auto_now=True, null=True, editable=False)

    code = models.CharField(max_length=50)
    utc_offset = models.SmallIntegerField()
    def __unicode__(self):
        return self.code

def _int_xor(i1, i2):
    """Return True if one and only one of i1 and i2 is zero."""
    return (i1 or i2) and not (i1 and i2)

class TimeStep(Lookup):
    length_minutes = models.PositiveIntegerField()
    length_months = models.PositiveSmallIntegerField()
    def __unicode__(self):
        return "(%d, %d)" % (self.length_minutes, self.length_months)
    def save(self, force_insert=False, force_update=False):
        if not _int_xor(self.length_minutes, self.length_months):
            raise Exception(_("%s is not a valid time step; exactly one of minutes and months must be zero") % self.__unicode__())
        super(TimeStep, self).save(force_insert, force_update)

# Function to call on Timeseries predelete to remove ts_records
def delete_ts_records(sender, instance, **kwargs):
    ts = timeseries.Timeseries(int(instance.id))
    ts.delete_from_db(db_connection)

class Timeseries(models.Model):
    # for db sync issues
    original_id = models.IntegerField(null=True, blank=True, editable=False)
    original_db = models.ForeignKey(Database, null=True, editable=False)
    last_modified = models.DateTimeField(auto_now=True, null=True, editable=False)

    gentity = models.ForeignKey(Gentity, related_name="timeseries")
    variable = models.ForeignKey(Variable)
    unit_of_measurement = models.ForeignKey(UnitOfMeasurement)
    name = models.CharField(max_length=200, blank=True)
    precision = models.SmallIntegerField(null=True, blank=True)
    time_zone = models.ForeignKey(TimeZone)
    remarks = models.TextField(blank=True)
    instrument = models.ForeignKey(Instrument, null=True, blank=True)
    time_step = models.ForeignKey(TimeStep, null=True, blank=True)
    nominal_offset_minutes = models.PositiveIntegerField(null=True, blank=True)
    nominal_offset_months = models.PositiveSmallIntegerField(null=True, blank=True)
    actual_offset_minutes = models.IntegerField(null=True, blank=True)
    actual_offset_months = models.SmallIntegerField(null=True, blank=True)
    class Meta:
        verbose_name = "Time Series"
        verbose_name_plural = "Time Series"
    @property
    def related_station(self):
        if self.gentity and self.gentity.__class__.__name__ == 'Station':
            return Station.objects.get(id=self.gentity.id)
        else:
            return None
    def __unicode__(self):
        return self.name
    def save(self, force_insert=False, force_update=False):
        if not self.time_step:
            if self.nominal_offset_minutes or self.nominal_offset_months \
            or self.actual_offset_minutes or self.actual_offset_months:
                raise Exception(_("Invalid time step: if time_step is null, offsets must also be null"))
        else:
            if self.actual_offset_minutes is None \
            or self.actual_offset_months is None:
                raise Exception(_("Invalid time step: if time_step is not null, actual offsets must be provided"))
            if (self.nominal_offset_minutes is None
                                and self.nominal_offset_months is not None) \
                        or (self.nominal_offset_minutes is not None
                                    and self.nominal_offset_Months is None):
                raise Exception(_("Invalid time step: nominal offsets must be both null or both not null"))
        super(Timeseries, self).save(force_insert, force_update)

signals.pre_delete.connect(delete_ts_records, Timeseries)

# Profile creation upon user registration
def user_post_save(sender, instance, **kwargs):
    profile, new = UserProfile.objects.get_or_create(user=instance)

def make_user_editor(sender, instance, **kwargs):
    user = instance
    if not user.is_superuser:
        group, created = Group.objects.get_or_create(name='editors')
        user.groups.add(group)

# Class for user profiles
class UserProfile(models.Model):
    user = models.ForeignKey(User, unique=True, verbose_name=_('Username'))
    fname = models.CharField(_('First Name'),null=True,blank=True, max_length=30)
    lname = models.CharField(_('Last Name'),null=True,blank=True, max_length=30)
    address = models.CharField(_('Location'),null=True,blank=True,max_length=100)
    organization = models.CharField(_('Organization'),null=True,blank=True,max_length=100)

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

if hasattr(settings, 'USERS_CAN_ADD_CONTENT')\
    and settings.USERS_CAN_ADD_CONTENT:
        signals.post_save.connect(make_user_editor, User)

from django.db.models.signals import post_syncdb
import enhydris.hcore.signals
post_syncdb.connect(enhydris.hcore.signals.after_syncdb)

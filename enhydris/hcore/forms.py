from django import forms
from django.conf import settings
from django.contrib.gis.geos import Point
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _

from ajax_select.fields import AutoCompleteSelectMultipleField
from captcha.fields import CaptchaField
from registration.forms import RegistrationFormTermsOfService

from pthelma import timeseries
from enhydris.hcore.widgets import SelectWithPop
from enhydris.hcore.models import (
    Station, Instrument, Person, Overseer, FileType, GentityFile,
    GentityGenericDataType, GentityGenericData, GentityAltCodeType,
    GentityAltCode, EventType, GentityEvent, Gentity, Gpoint,
    PoliticalDivision, WaterBasin, WaterDivision, Lentity, InstrumentType,
    TimeStep, Variable, UnitOfMeasurement, TimeZone, IntervalType, Timeseries)


class OverseerForm(ModelForm):

    station_objects = Station.objects.all()
    if len(settings.ENHYDRIS_SITE_STATION_FILTER) > 0:
        station_objects = station_objects.filter(
            **settings.ENHYDRIS_SITE_STATION_FILTER)
    station = forms.ModelChoiceField(station_objects, label='Station',
                                     empty_label=None)
    person = forms.ModelChoiceField(Person.objects,
                                    widget=SelectWithPop(model_name='person'))

    class Meta:
        model = Overseer
        exclude = []

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        gentity_id = kwargs.pop('gentity_id', None)
        super(OverseerForm, self).__init__(*args, **kwargs)

        if user and not user.is_superuser:
            perms = user.get_rows_with_permission(Station(), 'edit')
            ids = [p.object_id for p in perms]
            self.fields["station"].queryset = Station.objects.filter(
                id__in=ids)
        if gentity_id:
            self.fields["station"].queryset = Station.objects.filter(
                id=gentity_id)


class GentityFileForm(ModelForm):

    station_objects = Station.objects.all()
    if len(settings.ENHYDRIS_SITE_STATION_FILTER) > 0:
        station_objects = station_objects.filter(
            **settings.ENHYDRIS_SITE_STATION_FILTER)
    gentity = forms.ModelChoiceField(station_objects, label='Station',
                                     empty_label=None)
    file_type = forms.ModelChoiceField(
        FileType.objects, widget=SelectWithPop(model_name='filetype'))

    class Meta:
        model = GentityFile
        exclude = []

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        gentity_id = kwargs.pop('gentity_id', None)
        super(GentityFileForm, self).__init__(*args, **kwargs)

        if user and not user.is_superuser:
            perms = user.get_rows_with_permission(Station(), 'edit')
            ids = [p.object_id for p in perms]
            self.fields["gentity"].queryset = Station.objects.filter(
                id__in=ids)
        if gentity_id:
            self.fields["gentity"].queryset = Station.objects.filter(
                id=gentity_id)


class GentityGenericDataForm(ModelForm):

    station_objects = Station.objects.all()
    if len(settings.ENHYDRIS_SITE_STATION_FILTER) > 0:
        station_objects = station_objects.filter(
            **settings.ENHYDRIS_SITE_STATION_FILTER)
    gentity = forms.ModelChoiceField(station_objects, label='Station',
                                     empty_label=None)
    data_type = forms.ModelChoiceField(
        GentityGenericDataType.objects,
        label='Data type',
        widget=SelectWithPop(model_name='gentitygenericdatatype'))

    class Meta:
        model = GentityGenericData
        exclude = []

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        gentity_id = kwargs.pop('gentity_id', None)
        super(GentityGenericDataForm, self).__init__(*args, **kwargs)

        if user and not user.is_superuser:
            perms = user.get_rows_with_permission(Station(), 'edit')
            ids = [p.object_id for p in perms]
            self.fields["gentity"].queryset = Station.objects.filter(
                id__in=ids)
        if gentity_id:
            self.fields["gentity"].queryset = Station.objects.filter(
                id=gentity_id)


class GentityAltCodeForm(ModelForm):

    station_objects = Station.objects.all()
    if len(settings.ENHYDRIS_SITE_STATION_FILTER) > 0:
        station_objects = station_objects.filter(
            **settings.ENHYDRIS_SITE_STATION_FILTER)
    gentity = forms.ModelChoiceField(station_objects, label='Station',
                                     empty_label=None)
    type = forms.ModelChoiceField(
        GentityAltCodeType.objects,
        widget=SelectWithPop(model_name='gentityaltcodetype'))

    class Meta:
        model = GentityAltCode
        exclude = []

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        gentity_id = kwargs.pop('gentity_id', None)
        super(GentityAltCodeForm, self).__init__(*args, **kwargs)

        if user and not user.is_superuser:
            perms = user.get_rows_with_permission(Station(), 'edit')
            ids = [p.object_id for p in perms]
            self.fields["gentity"].queryset = Station.objects.filter(
                id__in=ids)
        if gentity_id:
            self.fields["gentity"].queryset = Station.objects.filter(
                id=gentity_id)


class GentityEventForm(ModelForm):

    station_objects = Station.objects.all()
    if len(settings.ENHYDRIS_SITE_STATION_FILTER) > 0:
        station_objects = station_objects.filter(
            **settings.ENHYDRIS_SITE_STATION_FILTER)
    gentity = forms.ModelChoiceField(station_objects, label='Station',
                                     empty_label=None)
    type = forms.ModelChoiceField(
        EventType.objects, widget=SelectWithPop(model_name='eventtype'))

    class Meta:
        model = GentityEvent
        exclude = []

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        gentity_id = kwargs.pop('gentity_id', None)
        super(GentityEventForm, self).__init__(*args, **kwargs)

        if user and not user.is_superuser:
            perms = user.get_rows_with_permission(Station(), 'edit')
            ids = [p.object_id for p in perms]
            self.fields["gentity"].queryset = Station.objects.filter(
                id__in=ids)
        if gentity_id:
            self.fields["gentity"].queryset = Station.objects.filter(
                id=gentity_id)


class GentityForm(ModelForm):

    class Meta:
        model = Gentity
        exclude = []


class GpointForm(GentityForm):
    abscissa = forms.FloatField(required=False)
    ordinate = forms.FloatField(required=False)
    srid = forms.IntegerField(required=False)

    class Meta:
        model = Gpoint
        exclude = ('point',)

    def clean(self):
        cleaned_data = self.cleaned_data
        if bool('abscissa' in cleaned_data and cleaned_data['abscissa']) ^ \
                bool('ordinate' in cleaned_data and cleaned_data['ordinate']):
            raise forms.ValidationError(_("Both coordinates (abscissa, "
                                          "ordinate) should be "
                                          "provided. If position is "
                                          "undefined, leave both empty."))
        if ('abscissa' in cleaned_data and cleaned_data['abscissa']) and not \
                ('srid' in cleaned_data and cleaned_data['srid']):
            self._errors['srid'] =\
                self.error_class(["Since you have provided coordinates, "
                                  "a srid should be provided as well. "
                                  "If you don't know about srid settings, "
                                  "see http://en.wikipedia.org/wiki/Srid/ . "
                                  "If you wish to enter geographical "
                                  "coordinates in WGS-84, you may "
                                  "enter a value of 4326 for srid."])
        super(GpointForm, self).clean()
        return cleaned_data

    def save(self, commit=True, *args, **kwargs):

        gpoint = super(GpointForm, self).save(commit=False)
        abscissa = self.cleaned_data['abscissa']
        ordinate = self.cleaned_data['ordinate']
        srid = self.cleaned_data['srid']

        if (abscissa is None) or (ordinate is None):
            gpoint.point = None
        else:
            if srid is None:
                srid = 4326
            gpoint.point = Point(x=abscissa, y=ordinate, srid=srid)

        # This may not be a good idea !
        if commit:
            gpoint.save()

        return gpoint


def StationForm(*args, **kwargs):
    """Return a form object.

    Think of StationForm as a class and instantiate it as if it were a class;
    the only thing this function does is define the class at instantiation
    time. The reason we do it this way is that we are using
    settings.ENHYDRIS_USERS_CAN_ADD_CONTENT at class definition time, and we
    want that setting to be overridable in unit tests.
    """

    class StationFormClass(GpointForm, GentityForm):
        """
        In this form, we overide the default fields with our own to allow
        inline creation of models that a Station has foreign keys to.

        To achieve this we use a custom widget which adds in each select box a
        'Add New' button which takes care of the object creation and also
        updating the original select box with the new entries. The only caveat
        is that we need to pass manually to the widget the name of the foreign
        object as it is depicted in our database in cases where the field name
        is not the same.
        """
        class Meta:
            model = Station
            exclude = ('overseers', 'creator', 'point')
            if not settings.ENHYDRIS_USERS_CAN_ADD_CONTENT:
                exclude = exclude + ('maintainers',)

        political_division = forms.ModelChoiceField(
            PoliticalDivision.objects,
            widget=SelectWithPop(model_name='politicaldivision'),
            required=False)
        water_basin = forms.ModelChoiceField(
            WaterBasin.objects,
            widget=SelectWithPop(model_name='waterbasin'),
            required=False)
        water_division = forms.ModelChoiceField(
            WaterDivision.objects,
            widget=SelectWithPop(model_name='waterdivision'),
            required=False)
        # owner should be modified to allow either Person or Organization add
        owner = forms.ModelChoiceField(
            Lentity.objects, widget=SelectWithPop(model_name='lentity'))

        if settings.ENHYDRIS_USERS_CAN_ADD_CONTENT:
            maintainers = AutoCompleteSelectMultipleField(
                'maintainers', required=False)

        def clean_altitude(self):
            value = self.cleaned_data['altitude']
            if value is not None and (value > 8850 or value < -422):
                raise forms.ValidationError(
                    _("%f is not a valid altitude") % (value,))
            return self.cleaned_data['altitude']

    return StationFormClass(*args, **kwargs)


class InstrumentForm(ModelForm):

    station_objects = Station.objects.all()
    if len(settings.ENHYDRIS_SITE_STATION_FILTER) > 0:
        station_objects = station_objects.filter(
            **settings.ENHYDRIS_SITE_STATION_FILTER)
    station = forms.ModelChoiceField(station_objects, label='Stations',
                                     empty_label=None)
    type = forms.ModelChoiceField(
        InstrumentType.objects,
        widget=SelectWithPop(model_name='instrumenttype'))

    class Meta:
        model = Instrument
        exclude = []

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        gentity_id = kwargs.pop('gentity_id', None)
        super(InstrumentForm, self).__init__(*args, **kwargs)

        if user and not user.is_superuser:
            perms = user.get_rows_with_permission(Station(), 'edit')
            ids = [p.object_id for p in perms]
            self.fields["station"].queryset = Station.objects.filter(
                id__in=ids)
        if gentity_id:
            self.fields["station"].queryset = Station.objects.filter(
                id=gentity_id)


def _int_xor(i1, i2):
    """Return True if one and only one of i1 and i2 is zero."""
    return (i1 or i2) and not (i1 and i2)


class TimeStepForm(ModelForm):

    class Meta:
        model = TimeStep
        exclude = []

    def clean(self):
        """
        This clean function ensures that length minutes and length months have
        valid values.
        """
        length_minutes = self.cleaned_data.get('length_minutes', None)
        length_months = self.cleaned_data.get('length_months', None)
        if not _int_xor(length_minutes, length_months):
            raise forms.ValidationError(
                _("Invalid timestep: exactly one of"
                  " minutes and months must be zero"))
        return self.cleaned_data


class TimeseriesForm(ModelForm):
    """
    This form extends the basic Timeseries model with a file field through
    which a user may upload additional data.
    """

    gentity = forms.ModelChoiceField(
        Gentity.objects.all(),
        empty_label=None,
        label='Station')
    instrument = forms.ModelChoiceField(
        Instrument.objects.all(),
        required=False,
        label='Instrument')
    variable = forms.ModelChoiceField(
        Variable.objects,
        widget=SelectWithPop(model_name='variable'))
    unit_of_measurement = forms.ModelChoiceField(
        UnitOfMeasurement.objects,
        widget=SelectWithPop(model_name='unitofmeasurement'))
    time_zone = forms.ModelChoiceField(
        TimeZone.objects,
        widget=SelectWithPop(model_name='timezone'))
    time_step = forms.ModelChoiceField(
        TimeStep.objects,
        widget=SelectWithPop(model_name='timestep'),
        required=False)
    interval_type = forms.ModelChoiceField(
        IntervalType.objects,
        required=False)

    class Meta:
        model = Timeseries
        exclude = []

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        gentity_id = kwargs.pop('gentity_id', None)
        instrument_id = kwargs.pop('instrument_id', None)
        super(TimeseriesForm, self).__init__(*args, **kwargs)

        if user and not user.is_superuser:
            perms = user.get_rows_with_permission(Station(), 'edit')
            ids = [p.object_id for p in perms]
            self.fields["gentity"].queryset = Station.objects.filter(
                id__in=ids)
            perms = user.get_rows_with_permission(Instrument(), 'edit')
            ids = [p.object_id for p in perms]
            self.fields["instrument"].queryset = Instrument.objects.filter(
                id__in=ids)
        if gentity_id:
            self.fields["gentity"].queryset = Station.objects.filter(
                id=gentity_id)
            self.fields["instrument"].queryset = Instrument.objects.filter(
                station__id=gentity_id)
        if instrument_id:
            self.fields["instrument"].queryset = Instrument.objects.filter(
                id=instrument_id)
            self.fields["instrument"].empty_label = None

    def clean_data(self):
        # Check if file contains valid timeseries data.
        if ('data' not in self.cleaned_data) or not self.cleaned_data['data']:
            return None
        self.cleaned_data['data'].seek(0)
        ts = timeseries.Timeseries()

        try:
            ts.read_file(self.cleaned_data['data'])
        except Exception as e:
            raise forms.ValidationError(str(e))

        return self.cleaned_data['data']

    def clean(self):
        """
        This function checks the timestep and offset values and reports
        inconsistencies.
        """
        time_step = self.cleaned_data.get('time_step', None)
        timestamp_rounding_minutes = self.cleaned_data.get(
            'timestamp_rounding_minutes', None)
        timestamp_rounding_months = self.cleaned_data.get(
            'timestamp_rounding_months', None)
        timestamp_offset_minutes = self.cleaned_data.get(
            'timestamp_offset_minutes', None)
        timestamp_offset_months = self.cleaned_data.get(
            'timestamp_offset_months', None)

        if (not time_step) and (
                timestamp_rounding_minutes or timestamp_rounding_months or
                timestamp_offset_minutes or timestamp_offset_months):
            raise forms.ValidationError(
                _("Invalid Timestep: If time step is"
                  " null, the rounding and offset must also be null"))
        elif time_step and (timestamp_offset_minutes is None or
                            timestamp_offset_months is None):
            raise forms.ValidationError(
                _("Invalid offset: If time step is"
                  " not null, timestamp offset values must be provided"))
        elif time_step and ((timestamp_rounding_minutes is None
                             and timestamp_rounding_months is not None) or
                            (timestamp_rounding_minutes is not None
                             and timestamp_rounding_months is None)):
            raise forms.ValidationError(
                _("Invalid rounding: both must be null or not null"))

        # add a validation test for instrument in station:
        instr = self.cleaned_data.get('instrument', None)
        if instr:
            stat = self.cleaned_data.get('gentity', None)
            assert(stat)
            if Instrument.objects.filter(id=instr.id,
                                         station__id=stat.id).count() < 1:
                raise forms.ValidationError(_("Selected instrument "
                                              "not in selected station"))

        # XXX: This is not a good idea but it's the only way to handle append
        # errors. We save the data in the clean function instead of the save
        # and if an error occurs we show the error in the form. Another way
        # would be to write a try_append() function in pthelma.timeseries but
        # this is specific to enhydris and should not be part of the pthelma
        # module.

        if 'data' in self.cleaned_data and self.cleaned_data['data']:
            data = self.cleaned_data['data']
            atimeseries = Timeseries.objects.get(pk=int(self.instance.id))
            data.seek(0)
            if self.cleaned_data['data_policy'] == 'A':
                try:
                    atimeseries.append_data(data)
                except Exception, e:
                    raise forms.ValidationError(_(e.message))

        return self.cleaned_data

    def save(self, commit=True, *args, **kwargs):

        tseries = super(TimeseriesForm, self).save(commit=False)

        # This may not be a good idea !
        if commit:
            tseries.save()

        # Handle pushing additional data if present back to the db
        if 'data' in self.cleaned_data and self.cleaned_data['data']:
            data = self.cleaned_data['data']
            data.seek(0)

            # Skip possible header
            while True:
                pos = data.tell()
                line = data.readline()
                if not line:
                    break
                if ('=' not in line) and (not line.isspace()):
                    data.seek(pos)
                    break

            if self.cleaned_data['data_policy'] == 'A':
                pass
                # ts.append_to_db(db.connection, commit=False)
            else:
                tseries.set_data(data)

        return tseries


class TimeseriesDataForm(TimeseriesForm):
    """
    Additional timeseries form to present the data upload fields
    """
    data = forms.FileField(required=False)
    data_policy = forms.ChoiceField(
        label=_('New data policy'),
        required=False,
        choices=(('A', 'Append to existing'),
                 ('O', 'Overwrite existing'),))


class RegistrationForm(RegistrationFormTermsOfService):
    """
    Extension of the default registration form to include a captcha
    """
    captcha = CaptchaField()

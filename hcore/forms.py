"""
Hcore Forms.
"""

from pthelma import timeseries
from django import forms, db
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.forms import ModelForm
from django.utils.translation import ugettext_lazy as _
from registration.forms import RegistrationForm
from ajax_select.fields import (AutoCompleteSelectMultipleField,
                                    AutoCompleteSelectField)
from enhydris.hcore.models import *
from enhydris.hcore.widgets import *




attrs_dict = { 'class': 'required' }

class HcoreRegistrationForm(RegistrationForm):
    """
    Extension of the default registration form to include a tos agreement
    (Terms of Service) and also require unique emails for each registration
    """
    tos = forms.BooleanField(widget=forms.CheckboxInput(attrs=attrs_dict),
                label=_(u'I have read and agree to the Terms of Service'),
                error_messages={ 'required': _("You must agree to the terms to register") })

    def clean_email(self):
        """
        Validate that the supplied email address is unique for the site.
        """
        if User.objects.filter(email__iexact=self.cleaned_data['email']):
            raise forms.ValidationError(_("This email address is already in use. Please supply a different email address."))
        return self.cleaned_data['email']

"""
Model forms.
"""

class OverseerForm(ModelForm):

    person = forms.ModelChoiceField(Person.objects,
                                widget=SelectWithPop(model_name='person'))

    class Meta:
        model = Overseer

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(OverseerForm, self).__init__(*args, **kwargs)

        if user and not user.is_superuser:
            perms = user.get_rows_with_permission(Station(), 'edit')
            ids = [ p.object_id for p in perms]
            self.fields["station"].queryset = Gentity.objects.filter(
                                                id__in=ids)




class GentityFileForm(ModelForm):

    file_type = forms.ModelChoiceField(FileType.objects,
                                widget=SelectWithPop(model_name='filetype'))

    class Meta:
        model = GentityFile

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(GentityFileForm, self).__init__(*args, **kwargs)

        if user and not user.is_superuser:
            perms = user.get_rows_with_permission(Station(), 'edit')
            ids = [ p.object_id for p in perms]
            self.fields["gentity"].queryset = Gentity.objects.filter(
                                                id__in=ids)

class GentityAltCodeForm(ModelForm):

    type = forms.ModelChoiceField(GentityAltCodeType.objects,
                      widget=SelectWithPop(model_name='gentityaltcodetype'))

    class Meta:
        model = GentityAltCode

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(GentityAltCodeForm, self).__init__(*args, **kwargs)

        if user and not user.is_superuser:
            perms = user.get_rows_with_permission(Station(), 'edit')
            ids = [ p.object_id for p in perms]
            self.fields["gentity"].queryset = Gentity.objects.filter(
                                                id__in=ids)


class GentityEventForm(ModelForm):

    type = forms.ModelChoiceField(EventType.objects,
                                widget=SelectWithPop(model_name='eventtype'))

    class Meta:
        model = GentityEvent

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(GentityEventForm, self).__init__(*args, **kwargs)

        if user and not user.is_superuser:
            perms = user.get_rows_with_permission(Station(), 'edit')
            ids = [ p.object_id for p in perms]
            self.fields["gentity"].queryset = Gentity.objects.filter(
                                                id__in=ids)




class GentityForm(ModelForm):
    class Meta:
        model = Gentity

class GpointForm(GentityForm):
    class Meta:
        model = Gpoint

class StationForm(GpointForm, GentityForm):
    """
    In this form, we overide the default fields with our own to allow inline
    creation of models that a Station has foreign keys to.

    To achieve this we use a custom widget which adds in each select box a 'Add
    New' button which takes care of the object creation and also updating the
    original select box with the new entries. The only caveat is that we need
    to pass manually to the widget the name of the foreign object as it is
    depicted in our database in cases where the field name is not the same.
    """
    class Meta:
        model = Station
        exclude = ('overseers','creator')

    political_division = forms.ModelChoiceField(PoliticalDivision.objects,
                                widget=SelectWithPop(model_name='politicaldivision'),required=False)
    water_basin = forms.ModelChoiceField(WaterBasin.objects,
                                widget=SelectWithPop(model_name='waterbasin'),required=False)
    water_division = forms.ModelChoiceField(WaterDivision.objects,
                                widget=SelectWithPop(model_name='waterdivision'),required=False)
    # owner should be modified to allow either Person or Organization add
    owner = forms.ModelChoiceField(Lentity.objects,
                                widget=SelectWithPop(model_name='lentity'))
    type = forms.ModelChoiceField(StationType.objects,
                                widget=SelectWithPop(model_name='stationtype'))


    if hasattr(settings, 'USERS_CAN_ADD_CONTENT')\
        and settings.USERS_CAN_ADD_CONTENT:
            maintainers = AutoCompleteSelectMultipleField('maintainers',
                                                         required=False)

    def clean_altitude(self):
        value = self.cleaned_data['altitude']
        if not value == None and (value > 8850 or value < -422):
            raise forms.ValidationError(_("%f is not a valid altitude") %
            (value,))
        return self.cleaned_data['altitude']

class InstrumentForm(ModelForm):
    station = forms.ModelChoiceField(Station.objects.all())
    type = forms.ModelChoiceField(InstrumentType.objects,
                                widget=SelectWithPop(model_name='instrumenttype'))
    class Meta:
        model = Instrument

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(InstrumentForm, self).__init__(*args, **kwargs)

        if user and not user.is_superuser:
            perms = user.get_rows_with_permission(Station(), 'edit')
            ids = [ p.object_id for p in perms]
            self.fields["station"].queryset = Station.objects.filter(
                                                id__in=ids)


def _int_xor(i1, i2):
    """Return True if one and only one of i1 and i2 is zero."""
    return (i1 or i2) and not (i1 and i2)

class TimeStepForm(ModelForm):
    """
    Form for TimeStep
    """

    class Meta:
        model = TimeStep


    def clean(self):
        """
        This clean function ensures that length minutes and length months have
        valid values.
        """
        length_minutes = self.cleaned_data.get('length_minutes', None)
        length_months = self.cleaned_data.get('length_months', None)
        if not _int_xor(length_minutes, length_months):
            raise forms.ValidationError(_("Invalid timestep: exactly one of"
                    " minutes and months must be zero"))

        return self.cleaned_data


class TimeseriesForm(ModelForm):
    """
    This form extends the basic Timeseries model with a file field through
    which a user may upload additional data.
    """

    gentity = forms.ModelChoiceField(Gentity.objects.all(),
                widget=SelectWithPop(model_name='gentity'))
    variable = forms.ModelChoiceField(Variable.objects,
                                widget=SelectWithPop(model_name='variable'))
    unit_of_measurement = forms.ModelChoiceField(UnitOfMeasurement.objects,
                                widget=SelectWithPop(model_name='unitofmeasurement'))
    time_zone = forms.ModelChoiceField(TimeZone.objects,
                                widget=SelectWithPop(model_name='timezone'))
    time_step = forms.ModelChoiceField(TimeStep.objects,
                                widget=SelectWithPop(model_name='timestep'),required=False)


    class Meta:
        model = Timeseries


    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(TimeseriesForm, self).__init__(*args, **kwargs)

        if user and not user.is_superuser:
            perms = user.get_rows_with_permission(Station(), 'edit')
            ids = [ p.object_id for p in perms]
            self.fields["gentity"].queryset = Gentity.objects.filter(
                                                id__in=ids)


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
        nominal_offset_minutes = self.cleaned_data.get('nominal_offset_minutes',
                                                             None)
        nominal_offset_months = self.cleaned_data.get('nominal_offset_months',
                                                             None)
        actual_offset_minutes = self.cleaned_data.get('actual_offset_minutes',
                                                             None)
        actual_offset_months = self.cleaned_data.get('actual_offset_months',
                                                             None)

        if not time_step:
            if nominal_offset_minutes or \
                nominal_offset_months or \
                actual_offset_minutes or \
                actual_offset_months:
                    raise forms.ValidationError(_("Invalid Timestep: If time step is"
                                           " null, the offsets must also be null!"))

        else:
            if actual_offset_minutes is None \
                or actual_offset_months is None:
                raise forms.ValidationError(_("Invalid offset: If time step is"
                         " not null, actual offset values must be provided!"))

            if (nominal_offset_minutes is None \
              and nominal_offset_months is not None) \
              or (nominal_offset_minutes is not None \
              and nominal_offset_months is None):
                raise forms.ValidationError(_("Invalid offsets: Nominal"
                              " offsets must be both null or both not null!"))


        # XXX: This is not a good idea but it's the only way to handle append
        # errors. We save the data in the clean function instead of the save
        # and if an error occurs we rollback the transaction and show the error
        # in the form. Another way would be to write a try_append() function in
        # pthelma.timeseries but this is specific to enhydris and should not be
        # part of the pthelma module.

        if 'data' in self.cleaned_data and self.cleaned_data['data']:
            ts = timeseries.Timeseries(int(self.instance.id))
            self.cleaned_data['data'].seek(0)
            ts.read_file(self.cleaned_data['data'])
            if self.cleaned_data['data_policy'] == 'A':
                try:
                    ts.append_to_db(db.connection, transaction=db.transaction)
                except Exception as e:
                    raise forms.ValidationError(_(e.message))

        return self.cleaned_data

    @db.transaction.commit_on_success
    def save(self, commit=True, *args,**kwargs):

        tseries = super(TimeseriesForm,self).save(commit=False)

        # This may not be a good idea !
        if commit:
            tseries.save()

        # Handle pushing additional data if present back to the db
        if 'data' in self.cleaned_data and self.cleaned_data['data']:
            ts = timeseries.Timeseries(int(self.instance.id))
            self.cleaned_data['data'].seek(0)
            ts.read_file(self.cleaned_data['data'])
            if self.cleaned_data['data_policy'] == 'A':
                pass
                # ts.append_to_db(db.connection, transaction=db.transaction)
            else:
                ts.write_to_db(db.connection, transaction=db.transaction)

        return tseries


class TimeseriesDataForm(TimeseriesForm):
    """
    Additional timeseries form to present the data upload fields
    """
    if hasattr(settings, 'STORE_TSDATA_LOCALLY') and\
        settings.STORE_TSDATA_LOCALLY:
        data = forms.FileField(required=False)
        data_policy = forms.ChoiceField(label=_('New data policy'),
                                        required=False,
                                        choices=(('A','Append to existing'),
                                             ('O','Overwrite existing'),))



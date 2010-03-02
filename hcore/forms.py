"""
Hcore Forms.
"""

import re
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
                                widget=SelectWithPop(model_name='politicaldivision'))
    water_basin = forms.ModelChoiceField(WaterBasin.objects,
                                widget=SelectWithPop(model_name='waterbasin'))
    water_division = forms.ModelChoiceField(WaterDivision.objects,
                                widget=SelectWithPop(model_name='waterdivision'))
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



class TimeseriesForm(ModelForm):
    """
    This form extends the basic Timeseries model with a file field through
    which a user may upload additional data.
    """
    gentity = forms.ModelChoiceField(Gentity.objects.all())
    data = forms.FileField(required=False)
    data_policy = forms.ChoiceField(label=_('New data policy'),
                                    choices=(('A','Append to existing'),
                                             ('O','Overwrite existing'),))


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
        # Here we should check if file contains valid timeseries data.
        if 'data' in self.cleaned_data:
            if not self.cleaned_data['data']:
                return None
            fdata = self.cleaned_data['data']
            fdata.seek(0)
            lines = len(fdata.readlines())

            if fdata.content_type != 'application/octet-stream':
                err_msg = _("File doesn\'t seem to be of the\
                                            appropriate type.")
                raise forms.ValidationError(err_msg)


            #check headers
            if lines < 15:
                err_msg = _("File doesn\'t seem to contain valid data.")
                raise forms.ValidationError(err_msg)

            #check all lines!
            fdata.seek(0)
            start = next(s for s in range(lines) if fdata.readline() == '\r\n')
            fdata.seek(0)
            adata = fdata.readlines()

            # start reading at start+1 (start is the empty line)
            for line in adata[start+1:]:
                if not re.match(
                    '^\d{4}-\d{2}-\d{2} (?:\d{2}:\d{2})?,(\d)*(?:\.\d+)?,'
                    '.*\r\n$', line):
                    err_msg = _("File doesn\'t seem to contain valid data.")
                    raise forms.ValidationError(err_msg)
            return self.cleaned_data["data"]

    @db.transaction.commit_manually
    def save(self, commit=True, *args,**kwargs):

        tseries = super(TimeseriesForm,self).save(commit=False)

        # This may not be a good idea !
        if commit:
            tseries.save()

        # Handle pushing additional data if present back to the db
        if self.cleaned_data['data']:
            ts = timeseries.Timeseries(int(self.instance.id))
            self.cleaned_data['data'].seek(0)
            lines = len(self.cleaned_data['data'].readlines())
            self.cleaned_data['data'].seek(0)
            start = next(s for s in range(lines) if self.cleaned_data['data'].readline() == '\r\n')
            self.cleaned_data['data'].seek(0)
            ts.read(self.cleaned_data['data'].readlines()[start+1:])
            if self.cleaned_data['data_policy'] == 'A':
                ts.append_to_db(db.connection, transaction=db.transaction)
            else:
                ts.write_to_db(db.connection, transaction=db.transaction)

        return tseries

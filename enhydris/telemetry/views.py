from django.contrib import messages
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import View

from rules.contrib.views import PermissionRequiredMixin

from enhydris.models import Station
from enhydris.telemetry import drivers
from enhydris.telemetry.forms import CommonDataForm
from enhydris.telemetry.models import Telemetry


class TelemetryWizardView(PermissionRequiredMixin, View):
    permission_required = "enhydris.change_station"

    def get_permission_object(self):
        return self.station

    def dispatch(self, request, *, station_id, seq):
        self.request = request
        self.station_id = station_id
        self.seq = seq
        self.station = Station.objects.get(pk=self.station_id)

        if not self.has_permission():
            raise Http404

        if seq == 1:
            wizard_step = WizardFirstStep(self.request, self.station, self.seq)
        else:
            wizard_step = WizardOtherStep(self.request, self.station, self.seq)

        return wizard_step.get_response()


class WizardStep:
    def __init__(self, request, station, seq):
        self.request = request
        self.station = station
        self.seq = seq

    @cached_property
    def configuration(self):
        return self.request.session.get(
            f"telemetry_{self.station.id}_configuration",
            {"station_id": self.station.id},
        )

    def copy_telemetry_data_from_database_to_session(self):
        try:
            telemetry = Telemetry.objects.get(station=self.station)
        except Telemetry.DoesNotExist:
            return
        keyprefix = f"telemetry_{self.station.id}_"
        vars = (
            "type",
            "data_time_zone",
            "fetch_interval_minutes",
            "fetch_offset_minutes",
            "fetch_offset_time_zone",
            "configuration",
        )
        for var in vars:
            self.request.session[f"{keyprefix}{var}"] = getattr(telemetry, var)

    def get_station_telemetry_data_from_session(self):
        keyprefix = f"telemetry_{self.station.id}_"
        n = len(keyprefix)
        return {
            key[n:]: value
            for key, value in self.request.session.items()
            if key.startswith(keyprefix)
        }


class WizardFirstStep(WizardStep):
    def get_response(self):
        form = self._get_form_from_request()
        if self.request.method == "POST" and form.is_valid():
            req = self.request
            for fieldname in form._meta.fields:
                key = f"telemetry_{self.station.id}_{fieldname}"
                req.session[key] = req.POST[fieldname]
            kwargs = {"station_id": self.station.id, "seq": 2}
            return HttpResponseRedirect(reverse("telemetry_wizard", kwargs=kwargs))
        return render(
            self.request,
            "enhydris/telemetry/wizard_step.html",
            {
                "station": self.station,
                "form": form,
                "seq": 1,
                "prev_seq": 0,
                "max_seq": 999,
            },
        )

    def _get_form_from_request(self):
        if self.request.method == "POST":
            form = CommonDataForm(self.request.POST)
        else:
            self.copy_telemetry_data_from_database_to_session()
            form = CommonDataForm(
                initial=self.get_station_telemetry_data_from_session()
            )
        return form


class WizardOtherStep(WizardStep):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_response(self):
        if f"telemetry_{self.station.id}_type" not in self.request.session:
            kwargs = {"station_id": self.station.id, "seq": 1}
            url = reverse("telemetry_wizard", kwargs=kwargs)
            return HttpResponseRedirect(url)

        self.telemetry_type = self.request.session[f"telemetry_{self.station.id}_type"]
        self.telemetry = drivers[self.telemetry_type]
        self.Form = self.telemetry.wizard_steps[self.seq - 2]
        return self._process_form()

    def _process_form(self):
        self.form = self._get_form_from_request()
        if self.request.method == "POST" and self.form.is_valid():
            return self._get_response_from_valid_form_submission()
        else:
            return render(
                self.request,
                "enhydris/telemetry/wizard_step.html",
                {
                    "station": self.station,
                    "form": self.form,
                    "seq": self.seq,
                    "prev_seq": self.seq - 1,
                    "max_seq": len(self.telemetry.wizard_steps) + 1,
                },
            )

    def _get_form_from_request(self):
        if self.request.method == "POST":
            form = self.Form(self.request.POST)
        else:
            form = self.Form(initial=self.configuration)
        return form

    def _get_response_from_valid_form_submission(self):
        self.configuration.update(self.form.cleaned_data)
        self.request.session[
            f"telemetry_{self.station.id}_configuration"
        ] = self.configuration
        if self.seq <= len(self.telemetry.wizard_steps):
            kwargs = {"station_id": self.station.id, "seq": self.seq + 1}
            target = reverse("telemetry_wizard", kwargs=kwargs)
        else:
            Telemetry.objects.filter(station=self.station).delete()
            kwargs = self.get_station_telemetry_data_from_session()
            Telemetry(station=self.station, **kwargs).save()
            msg = _("Telemetry has been configured")
            messages.add_message(self.request, messages.SUCCESS, msg)
            target = reverse("station_detail", kwargs={"pk": self.station.id})
        return HttpResponseRedirect(target)

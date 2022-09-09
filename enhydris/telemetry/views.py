from django.contrib import messages
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import View
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from rules.contrib.views import PermissionRequiredMixin

from enhydris.models import Station
from enhydris.telemetry import drivers
from enhydris.telemetry.forms import (
    ChooseSensorForm,
    ChooseStationForm,
    ConnectionDataForm,
    EssentialDataForm,
)
from enhydris.telemetry.models import Sensor, Telemetry, TelemetryLogMessage


class RedirectToFirstStep(Exception):
    """This is raised when we must redirect to the first step."""


class TelemetryWizardView(PermissionRequiredMixin, View):
    permission_required = "enhydris.change_station"
    forms = [EssentialDataForm, ConnectionDataForm, ChooseStationForm, ChooseSensorForm]

    def get_permission_object(self):
        return self.station

    def dispatch(self, request, *, station_id, seq):
        self.request = request
        self.station = Station.objects.get(pk=station_id)
        self.seq = seq

        self._check_permission()

        try:
            self.form = self._get_form_from_request()
        except RedirectToFirstStep:
            kwargs = {"station_id": self.station.id, "seq": 1}
            return HttpResponseRedirect(reverse("telemetry_wizard", kwargs=kwargs))

        if self.request.method == "POST" and self.form.is_valid():
            return self._process_valid_form_post()
        else:
            return self._process_get()

    def _get_form_from_request(self):
        Form = self.forms[self.seq - 1]

        if self.seq == 1:
            self.copy_telemetry_data_from_database_to_session()
        self.session_config = self._get_station_telemetry_data_from_session()
        self.driver = drivers.get(self.session_config["type"])

        if self.request.method == "POST":
            form = Form(
                self.request.POST,
                initial=self.session_config,
                driver=self.driver,
                station=self.station,
            )
        else:
            form = Form(
                initial=self.session_config, driver=self.driver, station=self.station
            )
        return form

    def copy_telemetry_data_from_database_to_session(self):
        default_data = {
            "type": None,
            "data_time_zone": None,
            "fetch_interval_minutes": None,
            "fetch_offset_minutes": None,
            "fetch_offset_time_zone": None,
            "additional_config": {},
        }
        key = f"telemetry_{self.station.id}"
        try:
            telemetry = Telemetry.objects.get(station=self.station)
        except Telemetry.DoesNotExist:
            self.request.session[key] = default_data
            return
        self.request.session[key] = {
            var: getattr(telemetry, var) for var in default_data
        }

    def _check_permission(self):
        if not self.has_permission():
            raise Http404

    def _process_valid_form_post(self):
        if self.seq == 1:
            return self._process_valid_form_post_of_step_1()
        else:
            return self._process_valid_form_post_of_step_gte_2()

    def _process_valid_form_post_of_step_1(self):
        self._update_session_data(self.form.cleaned_data)
        kwargs = {"station_id": self.station.id, "seq": 2}
        return HttpResponseRedirect(reverse("telemetry_wizard", kwargs=kwargs))

    def _process_valid_form_post_of_step_gte_2(self):
        self._update_session_data(self.form.cleaned_data)
        if self.seq < len(self.forms):
            # Non-final step
            kwargs = {"station_id": self.station.id, "seq": self.seq + 1}
            target = reverse("telemetry_wizard", kwargs=kwargs)
        else:
            # Final step
            Telemetry.objects.filter(station=self.station).delete()
            session_config = self._get_station_telemetry_data_from_session()
            self._save_to_database(session_config)
            msg = _("Telemetry has been configured")
            messages.add_message(self.request, messages.SUCCESS, msg)
            target = reverse("station_detail", kwargs={"pk": self.station.id})
        return HttpResponseRedirect(target)

    def _update_session_data(self, data):
        key = f"telemetry_{self.station.id}"
        session_config = self.request.session[key]
        session_config.update(data)
        self.request.session[key] = session_config

    def _save_to_database(self, config):
        sensors_config = {
            k: v for k, v in config.items() if k.startswith("sensor_") and v
        }
        other_config = {k: v for k, v in config.items() if not k.startswith("sensor_")}
        Telemetry.objects.filter(station=self.station).delete()
        telemetry = Telemetry.objects.create(station=self.station, **other_config)
        for key, value in sensors_config.items():
            remote_sensor_id = key.partition("_")[2]
            Sensor.objects.create(
                telemetry=telemetry,
                sensor_id=remote_sensor_id,
                timeseries_group_id=value,
            )

    def _process_get(self):
        return render(
            self.request,
            "enhydris/telemetry/wizard_step.html",
            {
                "station": self.station,
                "form": self.form,
                "seq": self.seq,
                "prev_seq": self.seq - 1,
                "max_seq": len(self.forms),
            },
        )

    def _get_station_telemetry_data_from_session(self):
        key = f"telemetry_{self.station.id}"
        try:
            return self.request.session[key]
        except KeyError:
            raise RedirectToFirstStep()


class TelemetryLogsView(PermissionRequiredMixin, ListView):
    permission_required = "enhydris.change_station"
    model = TelemetryLogMessage
    template_name = "enhydris/telemetry/telemetrylogmessage_list.html"
    paginate_by = 100

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.station = Station.objects.get(id=self.kwargs["station_id"])

    def get_permission_object(self):
        return self.station

    def get_queryset(self):
        result = super().get_queryset()
        result = result.filter(telemetry__station=self.station)
        return result

    def get_context_data(self):
        result = super().get_context_data()
        result["station"] = self.station
        return result


class TelemetryLogDetailView(PermissionRequiredMixin, DetailView):
    permission_required = "enhydris.change_station"
    model = TelemetryLogMessage
    template_name = "enhydris/telemetry/telemetrylogmessage_detail.html"

    def get_permission_object(self):
        return Station.objects.get(id=self.kwargs["station_id"])

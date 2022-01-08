from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic.base import View

from enhydris.models import Station
from enhydris.telemetry import drivers
from enhydris.telemetry.forms import CommonDataForm
from enhydris.telemetry.models import Telemetry


class TelemetryWizardView(View):
    def dispatch(self, request, *, station_id, seq):
        self.request = request
        self.station_id = station_id
        self.seq = seq
        self.station = Station.objects.get(pk=self.station_id)

        if seq == 1:
            return self.dispatch_first_step()

        if f"telemetry_{station_id}_type" not in request.session:
            kwargs = {"station_id": station_id, "seq": 1}
            url = reverse("telemetry_wizard", kwargs=kwargs)
            return HttpResponseRedirect(url)

        self.telemetry_type = request.session[f"telemetry_{station_id}_type"]
        self.telemetry = drivers[self.telemetry_type]
        return self.dispatch_other_step()

    def dispatch_first_step(self):
        if self.request.method == "POST":
            form = CommonDataForm(self.request.POST)
            if form.is_valid():
                req = self.request
                for fieldname in form._meta.fields:
                    key = f"telemetry_{self.station_id}_{fieldname}"
                    req.session[key] = req.POST[fieldname]
                kwargs = {"station_id": self.station_id, "seq": 2}
                return HttpResponseRedirect(reverse("telemetry_wizard", kwargs=kwargs))
        else:
            self.copy_telemetry_data_from_database_to_session()
            form = CommonDataForm(
                initial=self.get_station_telemetry_data_from_session()
            )
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

    def dispatch_other_step(self):
        station_id = self.station_id
        configuration = self.request.session.get(
            f"telemetry_{station_id}_configuration", {"station_id": station_id}
        )
        Form = self.telemetry.wizard_steps[self.seq - 2]
        if self.request.method == "POST":
            form = Form(self.request.POST, initial=configuration)
            if form.is_valid():
                configuration.update(form.cleaned_data)
                self.request.session[
                    f"telemetry_{station_id}_configuration"
                ] = configuration
                if self.seq <= len(self.telemetry.wizard_steps):
                    kwargs = {"station_id": self.station_id, "seq": self.seq + 1}
                    target = reverse("telemetry_wizard", kwargs=kwargs)
                else:
                    Telemetry.objects.filter(station=self.station).delete()
                    kwargs = self.get_station_telemetry_data_from_session()
                    Telemetry(station=self.station, **kwargs).save()
                    msg = _("Telemetry has been configured")
                    messages.add_message(self.request, messages.SUCCESS, msg)
                    target = reverse("station_detail", kwargs={"pk": self.station_id})
                return HttpResponseRedirect(target)
        else:
            form = Form(initial=configuration)
        return render(
            self.request,
            "enhydris/telemetry/wizard_step.html",
            {
                "station": self.station,
                "form": form,
                "seq": self.seq,
                "prev_seq": self.seq - 1,
                "max_seq": len(self.telemetry.wizard_steps) + 1,
            },
        )

    def copy_telemetry_data_from_database_to_session(self):
        try:
            telemetry = Telemetry.objects.get(station=self.station)
        except Telemetry.DoesNotExist:
            return
        keyprefix = f"telemetry_{self.station_id}_"
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
        keyprefix = f"telemetry_{self.station_id}_"
        n = len(keyprefix)
        return {
            key[n:]: value
            for key, value in self.request.session.items()
            if key.startswith(keyprefix)
        }

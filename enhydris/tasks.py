import os
import textwrap

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils.translation import ugettext_lazy as _

import celery

from enhydris.celery import app
from enhydris.models import Timeseries


class SaveTimeseriesData(celery.Task):
    def read_arguments(self, *, id, replace_or_append, datafilename, username):
        self.timeseries = Timeseries.objects.get(id=id)
        self.replace_or_append = replace_or_append
        self.datafilename = datafilename
        self.user = User.objects.get(username=username)

    def import_timeseries(self):
        try:
            with open(self.datafilename, newline="\n") as f:
                if self.replace_or_append == "APPEND":
                    self.timeseries.append_data(f)
                else:
                    self.timeseries.set_data(f)
        finally:
            os.unlink(self.datafilename)

    def send_notification(self):
        msg = _('Time series "{}" was imported successfully').format(
            self._timeseries_name
        )
        send_mail(msg, msg, settings.DEFAULT_FROM_EMAIL, [self.user.email])

    def on_failure(self, *args, **kwargs):
        subject = _('Importing time series "{}" failed').format(self._timeseries_name)
        msg = _(
            textwrap.dedent(
                """
                The time series "{}"
                failed to import. This should not happen.  Details about the
                error have been emailed to the administrators.

                Please retry in a few minutes. If the error persists, try again
                in a few days; the administrators will hopefully fix it.
                """
            ).format(self._timeseries_name)
        )
        send_mail(subject, msg, settings.DEFAULT_FROM_EMAIL, [self.user.email])

    @property
    def _timeseries_name(self):
        t = self.timeseries
        return f"{t.timeseries_group.gentity.name} - {t.timeseries_group} - {t}"


@app.task(bind=True, base=SaveTimeseriesData)
def save_timeseries_data(self, **kwargs):
    self.read_arguments(**kwargs)
    self.import_timeseries()
    self.send_notification()

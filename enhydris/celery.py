# Enhydris on its own does not use Celery (and it's not listed in requirements.txt).
# However, Celery is used by some add-on apps like enhydris-autoprocess and
# enhydris-synoptic. To simplify setup and use a single set of celery workers for all
# such apps, we don't specify a celery "app" in the plugin; just a single celery app
# here that autodiscovers all tasks.

import socket
import textwrap

from django.conf import settings
from django.core.mail import mail_admins

from celery import Celery
from celery.signals import task_failure

from enhydris import set_django_settings_module

set_django_settings_module()

app = Celery("enhydris")

app.config_from_object("django.conf:settings")
app.autodiscover_tasks()


@task_failure.connect()
def email_failed_task(**kwargs):
    if not settings.ENHYDRIS_CELERY_SEND_TASK_ERROR_EMAILS:
        return
    subject = "[celery@{host}] {sender.name}: {exception}".format(
        host=socket.gethostname(), **kwargs
    )
    message = textwrap.dedent(
        """\
        Task id: {task_id}

        {einfo}
        """
    ).format(**kwargs)
    mail_admins(subject, message)

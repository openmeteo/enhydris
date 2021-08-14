# Celery is used both by Enhydris and by some add-on apps like enhydris-autoprocess and
# enhydris-synoptic. To simplify setup and use a single set of celery workers for all
# such apps, "tasks.py" (of Enhydris or of the add-on) can import the celery "app" from
# this file, like this:
#
#     from enhydris.celery import app
#
#     @app.task
#     def mytask():
#         ...
#
# The tasks in any add-on are autodiscovered by this "app". In addition, any exceptions
# occurring during task execution are emailed to the ADMINS.

import socket
import textwrap

from django.conf import settings
from django.core.mail import mail_admins

from celery import Celery
from celery.signals import task_failure

from enhydris import set_django_settings_module

set_django_settings_module()

app = Celery("enhydris")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@task_failure.connect()
def email_failed_task(**kwargs):
    if not settings.ENHYDRIS_CELERY_SEND_TASK_ERROR_EMAILS:
        return
    subject = "[celery@{host}] {sender.name}: {exception.__class__.__name__}".format(
        host=socket.gethostname(), **kwargs
    )
    message = textwrap.dedent(
        """\
        Task id: {task_id}

        {einfo}
        """
    ).format(**kwargs)
    mail_admins(subject, message)

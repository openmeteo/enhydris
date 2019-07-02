# Enhydris on its own does not use Celery (and it's not listed in requirements.txt).
# However, Celery is used by some add-on apps like enhydris-autoprocess and
# enhydris-synoptic. To simplify setup and use a single set of celery workers for all
# such apps, we don't specify a celery "app" in the plugin; just a single celery app
# here that autodiscovers all tasks.

from celery import Celery

from enhydris import set_django_settings_module

set_django_settings_module()

app = Celery("enhydris")

app.config_from_object("django.conf:settings")
app.autodiscover_tasks()

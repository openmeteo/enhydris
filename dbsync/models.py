from django.db import models
from django.utils.translation import ugettext_lazy as _

class Database(models.Model):
    """
    This class holds information for the database synchronization. Each db in
    the sync pool must have a corresponding entry here.
    """
    name = models.CharField(max_length=64, blank=True)
    ip_address = models.CharField(_('IP address'), max_length=16)
    hostname = models.CharField(_('Hostname'),unique=True, max_length=255)
    descr = models.TextField(_('Description'),max_length=255, blank=True)
    last_sync = models.DateTimeField(null=True, editable=False)

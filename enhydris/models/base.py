from django.contrib.gis.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _


class Lookup(models.Model):
    last_modified = models.DateTimeField(default=now, null=True, editable=False)
    descr = models.CharField(max_length=200, blank=True, verbose_name=_("Description"))

    class Meta:
        abstract = True
        ordering = ("descr",)

    def __str__(self):
        return self.descr

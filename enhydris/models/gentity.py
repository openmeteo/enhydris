from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.gis.db import models
from django.contrib.sites.managers import CurrentSiteManager
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy

from .base import Lookup
from .lentity import Lentity


class Gentity(models.Model):
    last_modified = models.DateTimeField(default=now, null=True, editable=False)
    name = models.CharField(max_length=200, blank=True, verbose_name=_("Name"))
    code = models.CharField(max_length=50, blank=True, verbose_name=_("Code"))
    remarks = models.TextField(blank=True, verbose_name=_("Remarks"))
    geom = models.GeometryField()
    sites = models.ManyToManyField(Site)

    class Meta:
        verbose_name_plural = "Gentities"
        ordering = ("name",)

    def __str__(self):
        return self.name or self.code or str(self.id)

    def save(self, *args, **kwargs):
        inserting = self._state.adding
        super().save(*args, **kwargs)
        if inserting:
            sites = settings.ENHYDRIS_SITES_FOR_NEW_STATIONS.copy()
            sites.add(Site.objects.get_current())
            self.sites.set(sites)


class Gpoint(Gentity):
    original_srid = models.IntegerField(
        null=True, blank=True, verbose_name=_("Original SRID")
    )
    altitude = models.FloatField(null=True, blank=True, verbose_name=_("Altitude"))
    f_dependencies = ["Gentity"]

    def original_abscissa(self):
        if self.original_srid:
            (x, y) = self.geom.transform(self.original_srid, clone=True)
            return round(x, 2) if abs(x) > 180 and abs(y) > 90 else x
        else:
            return self.geom.x

    def original_ordinate(self):
        if self.original_srid:
            (x, y) = self.geom.transform(self.original_srid, clone=True)
            return round(y, 2) if abs(x) > 180 and abs(y) > 90 else y
        else:
            return self.geom.y


class GareaCategory(Lookup):
    class Meta:
        verbose_name = _("Area category")
        verbose_name_plural = _("Area categories")


class Garea(Gentity):
    category = models.ForeignKey(
        GareaCategory, on_delete=models.CASCADE, verbose_name=_("Category")
    )
    f_dependencies = ["Gentity"]

    class Meta:
        verbose_name = _("Area")
        verbose_name_plural = _("Areas")


class RelatedStationMixin:
    @property
    def related_station(self):
        try:
            return Station.objects.get(id=self.gentity.id)
        except Station.DoesNotExist:
            return None


class GentityImage(models.Model, RelatedStationMixin):
    last_modified = models.DateTimeField(default=now, null=True, editable=False)
    gentity = models.ForeignKey(Gentity, on_delete=models.CASCADE)
    date = models.DateField(blank=True, null=True, verbose_name=_("Date"))
    content = models.ImageField(upload_to="gentityfile", verbose_name=_("Content"))
    descr = models.CharField(max_length=100, blank=True, verbose_name=_("Description"))
    remarks = models.TextField(blank=True, verbose_name=_("Remarks"))
    featured = models.BooleanField(default=False, verbose_name=_("Featured"))

    class Meta:
        verbose_name = _("Image")
        verbose_name_plural = _("Images")
        ordering = ("-featured", "date", "descr")

    def __str__(self):
        return (
            self.descr or (self.date and self.date.date().isoformat()) or str(self.id)
        )


class GentityFile(models.Model, RelatedStationMixin):
    last_modified = models.DateTimeField(default=now, null=True, editable=False)
    gentity = models.ForeignKey(Gentity, on_delete=models.CASCADE)
    date = models.DateField(blank=True, null=True, verbose_name=_("Date"))
    content = models.FileField(upload_to="gentityfile", verbose_name=_("Content"))
    descr = models.CharField(max_length=100, verbose_name=_("Description"))
    remarks = models.TextField(blank=True, verbose_name=_("Remarks"))

    class Meta:
        verbose_name = _("File")
        verbose_name_plural = _("Files")
        ordering = ("descr",)

    def __str__(self):
        return self.descr or str(self.id)


class EventType(Lookup):
    class Meta:
        verbose_name = _("Log entry type")
        verbose_name_plural = _("Log entry types")


class GentityEvent(models.Model):
    last_modified = models.DateTimeField(default=now, null=True, editable=False)
    gentity = models.ForeignKey(Gentity, on_delete=models.CASCADE)
    date = models.DateField(verbose_name=_("Date"))
    type = models.ForeignKey(
        EventType, on_delete=models.CASCADE, verbose_name=_("Type")
    )
    user = models.CharField(blank=True, max_length=64, verbose_name=_("User"))
    report = models.TextField(blank=True, verbose_name=_("Report"))

    class Meta:
        verbose_name = _("Log entry")
        verbose_name_plural = _("Log entries")
        ordering = ["-date"]

    def __str__(self):
        return str(self.date) + " " + self.type.__str__()

    @property
    def related_station(self):
        try:
            return Station.objects.get(id=self.gentity.id)
        except Station.DoesNotExist:
            return None


class Station(Gpoint):
    owner = models.ForeignKey(
        Lentity,
        related_name="owned_stations",
        on_delete=models.CASCADE,
        verbose_name=pgettext_lazy("Entity that owns the station", "Owner"),
    )
    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("Station start date", "Start date"),
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=pgettext_lazy("Station end date", "End date"),
    )
    overseer = models.CharField(max_length=30, blank=True, verbose_name=_("Overseer"))
    # The following two fields are only useful when USERS_CAN_ADD_CONTENT
    # is set.
    creator = models.ForeignKey(
        User,
        null=True,
        blank=True,
        related_name="created_stations",
        on_delete=models.CASCADE,
        verbose_name=pgettext_lazy(
            "User who has full permissions on station", "Administrator"
        ),
    )
    maintainers = models.ManyToManyField(
        User,
        blank=True,
        related_name="maintaining_stations",
        verbose_name=_("Maintainers"),
    )

    objects = models.Manager()
    on_site = CurrentSiteManager()
    f_dependencies = ["Gpoint"]

    class Meta:
        verbose_name = _("Station")
        verbose_name_plural = _("Stations")

    @property
    def last_update_naive(self):
        def get_last_update_naive():
            result = self.last_update
            if result is not None:
                result = result.replace(tzinfo=None)
            return result

        return cache.get_or_set(
            f"station_last_update_naive_{self.id}", get_last_update_naive
        )

    @property
    def last_update(self):
        def get_last_update():
            from .timeseries import Timeseries

            timeseries = Timeseries.objects.filter(timeseries_group__gentity_id=self.id)
            result = None
            for t in timeseries:
                t_end_date = t.end_date
                if t_end_date is None:
                    continue
                if result is None or t_end_date > result:
                    result = t_end_date
            return result

        return cache.get_or_set(f"station_last_update_{self.id}", get_last_update)

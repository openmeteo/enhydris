from django.contrib.gis.db import models
from django.db.models.signals import post_save
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _


def post_save_person_or_organization(sender, **kwargs):
    """Create and save ordering_string upon saving a person or organization.

    When we want to sort a list of lentities that has both people and organizations,
    we need a common sorting field. We calculate and save this sorting field upon
    saving the person or organization.
    """
    instance = kwargs["instance"]
    try:
        string = instance.name
    except AttributeError:
        string = "{} {}".format(instance.last_name, instance.first_name)
    lentity = instance.lentity_ptr
    lentity.ordering_string = string
    super(Lentity, lentity).save()


class Lentity(models.Model):
    last_modified = models.DateTimeField(default=now, null=True, editable=False)
    remarks = models.TextField(blank=True, verbose_name=_("Remarks"))
    ordering_string = models.CharField(
        max_length=255, null=True, blank=True, editable=False
    )

    class Meta:
        verbose_name_plural = "Lentities"
        ordering = ("ordering_string",)

    def __str__(self):
        return self.ordering_string or str(self.pk)


class Person(Lentity):
    last_name = models.CharField(
        max_length=100, blank=True, verbose_name=_("Last name")
    )
    first_name = models.CharField(
        max_length=100, blank=True, verbose_name=_("First name")
    )
    middle_names = models.CharField(
        max_length=100, blank=True, verbose_name=_("Middle names")
    )
    initials = models.CharField(max_length=20, blank=True, verbose_name=_("Initials"))
    f_dependencies = ["Lentity"]

    class Meta:
        verbose_name = _("Person")
        verbose_name_plural = _("Persons")
        ordering = ("last_name", "first_name")

    def __str__(self):
        return self.last_name + " " + self.initials


post_save.connect(post_save_person_or_organization, sender=Person)


class Organization(Lentity):
    name = models.CharField(max_length=200, blank=True, verbose_name=_("Name"))
    acronym = models.CharField(max_length=50, blank=True, verbose_name=_("Acronym"))
    f_dependencies = ["Lentity"]

    class Meta:
        verbose_name = _("Organization")
        verbose_name_plural = _("Organization")
        ordering = ("name",)

    def __str__(self):
        return self.acronym if self.acronym else self.name


post_save.connect(post_save_person_or_organization, sender=Organization)

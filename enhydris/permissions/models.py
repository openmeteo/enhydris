from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.auth.models import User, Group


class Permission(models.Model):
    name = models.CharField(max_length=16)
    content_type = models.ForeignKey(ContentType,
                                     related_name="row_permissions")
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    user = models.ForeignKey(User, null=True, blank=True)
    group = models.ForeignKey(Group, null=True, blank=True)

    class Meta:
        verbose_name = 'permission'
        verbose_name_plural = 'permissions'

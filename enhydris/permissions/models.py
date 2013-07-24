from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.contrib.auth.models import User, Group
from django.contrib import admin

class Permission(models.Model):
    name = models.CharField(max_length=16)
    content_type = models.ForeignKey(ContentType, related_name="row_permissions")
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    user = models.ForeignKey(User, null=True)
    group = models.ForeignKey(Group, null=True)

    class Meta:
        verbose_name = 'permission'
        verbose_name_plural = 'permissions'

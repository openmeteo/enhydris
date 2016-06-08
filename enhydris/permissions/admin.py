from django.contrib import admin
from enhydris.permissions.models import Permission


class PermissionAdmin(admin.ModelAdmin):
    model = Permission
    list_display = ('content_type', 'user', 'group', 'name')
    list_filter = ('name',)
    search_fields = ['object_id', 'content_type', 'user', 'group']
    raw_id_fields = ['user', 'group']

    def __str__(self):
        return "%s | %s | %d | %s" % (
            self.content_type.app_label, self.content_type, self.object_id,
            self.name)

admin.site.register(Permission, PermissionAdmin)

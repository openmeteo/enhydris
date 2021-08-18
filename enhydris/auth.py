import django.contrib.auth.backends
from django.contrib.sites.models import Site


class AuthBackend(django.contrib.auth.backends.ModelBackend):
    def authenticate(self, *args, **kwargs):
        user = super().authenticate(*args, **kwargs)
        if user is None:
            return
        current_domain = Site.objects.get_current().domain
        if user.is_superuser or user.groups.filter(name=current_domain).exists():
            return user

# We use a different file for the dj_rest_auth-related serializers because we need to
# import RegisterSerializer. If it's put in serializers.py, it somehow causes errors in
# unit tests that attempt to import it (the error is "ProgrammingError: relation
# "django_site" does not exist").  Apparently this is because objects for django_site
# are being accessed before the table has been created. Possibly a dj_rest_auth bug.

from django.utils.translation import gettext as _
from rest_framework import serializers

import rest_captcha.serializers
import rest_captcha.utils
from dj_rest_auth.registration.serializers import RegisterSerializer

# The following class should probably be
#     class RegisterWithCaptchaSerializer(RegisterSerializer, RestCaptchaSerializer):
#         pass
# However, RestCaptchaSerializer appears to be buggy (as of 0.1.0), so we reimplement
# it here. (The bug seems to be that it removes "captcha_key" and "captcha_value"
# from data, which subsequently causes an error during later processing by DRF.)


class RegisterWithCaptchaSerializer(RegisterSerializer):
    captcha_key = serializers.CharField(max_length=64)
    captcha_value = serializers.CharField(max_length=8, trim_whitespace=True)

    def validate(self, data):
        super().validate(data)
        cache_key = rest_captcha.utils.get_cache_key(data["captcha_key"])
        real_value = rest_captcha.serializers.cache.get(cache_key)
        if real_value is None:
            raise serializers.ValidationError(_("Invalid or expired captcha key"))
        rest_captcha.serializers.cache.delete(cache_key)
        if data["captcha_value"].upper() != real_value:
            raise serializers.ValidationError(_("Invalid captcha value"))
        return data

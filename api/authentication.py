"""
Custom authentication mechanism for Piston API
"""

import binascii

from django.http import HttpResponse
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import authenticate

class RemoteInstanceAuthentication(object):
    """
    Authenticator for remote instances. Used when pulling timeseries data.

    Remote user must also be local superuser or he gets a 403 error.
    """

    def __init__(self,auth_func=authenticate,realm="API"):
        self.realm = realm
        self.auth_func = auth_func

    def is_authenticated(self, request):
        auth_string = request.META.get('HTTP_AUTHORIZATION', None)

        if not auth_string:
            return False

        try:
            (authmeth, auth) = auth_string.split(" ", 1)

            if not authmeth.lower() == 'basic':
                return False

            auth = auth.strip().decode('base64')
            (username, password) = auth.split(':', 1)
        except (ValueError, binascii.Error):
            return False

        request.user = self.auth_func(username=username, password=password) \
            or AnonymousUser()

        return not request.user in (False, None, AnonymousUser()) and\
                request.user.is_superuser

    def challenge(self):
        """
        `challenge`: In cases where `is_authenticated` returns
        False, the result of this method will be returned.
        This will usually be a `HttpResponse` object with
        some kind of challenge headers and 401 code on it.
        """
        resp = HttpResponse("Authorization Required")
        resp['WWW-Authenticate'] = 'Basic realm="%s"' % self.realm
        resp.status_code = 401
        return resp

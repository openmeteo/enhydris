from urllib.parse import urlencode

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect


class AuthenticationRequired(Exception):
    pass


class GlobalLoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            self._check_for_user_login(request)
        except AuthenticationRequired:
            return self._authentication_required_response(request)

        return self.get_response(request)

    def _check_for_user_login(self, request):
        auth_required_setting = settings.ENHYDRIS_AUTHENTICATION_REQUIRED
        if not auth_required_setting or request.user.is_authenticated:
            return
        self._ensure_view_is_allowed_unauthenticated(request)

    def _ensure_view_is_allowed_unauthenticated(self, request):
        allowed_views = [
            settings.LOGIN_URL,
            "/accounts/password/reset/",
            "/api/",
        ]
        is_allowed_view = any([request.path.startswith(x) for x in allowed_views])
        if not is_allowed_view:
            raise AuthenticationRequired()

    def _authentication_required_response(self, request):
        if request.path.startswith("/api/"):
            return HttpResponse("Authentication required", status=401)
        else:
            next_url = request.get_full_path()
            redirect_url = f"{settings.LOGIN_URL}?{urlencode({'next': next_url})}"
            return redirect(redirect_url)

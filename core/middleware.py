from django.conf import settings
from django.shortcuts import redirect, resolve_url

from core.exceptions import WIPFeatureError
from core.views import Custom503View


class WIPMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        if isinstance(exception, WIPFeatureError):
            view = Custom503View.as_view()
            return view(request, exception=exception)
        return None


class AuthenticationRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.exempt_paths = {
            resolve_url("login"),
            resolve_url("external_auth:discord_login"),
            resolve_url("external_auth:discord_callback"),
        }
        self.exempt_prefixes = [
            settings.STATIC_URL,
            getattr(settings, "MEDIA_URL", None),
        ]

    def __call__(self, request):
        if request.user.is_authenticated:
            return self.get_response(request)

        if request.path in self.exempt_paths:
            return self.get_response(request)

        for prefix in self.exempt_prefixes:
            if prefix and request.path.startswith(prefix):
                return self.get_response(request)

        login_url = resolve_url(settings.LOGIN_URL)
        return redirect(f"{login_url}?next={request.get_full_path()}")

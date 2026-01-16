from django.conf import settings
from django.shortcuts import redirect, resolve_url
from django.utils.deprecation import MiddlewareMixin

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

class AuthenticationRequiredMiddleware(MiddlewareMixin):
    def __init__(self, get_response=None):
        super().__init__(get_response)
        self.exempt_prefixes = [
            settings.STATIC_URL,
            settings.MEDIA_URL,
            '/api/'
        ]

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.user.is_authenticated:
            return None

        if getattr(view_func, "is_public", False):
            return None

        view_class = getattr(view_func, "view_class", None)
        if view_class and getattr(view_class, "is_public", False):
            return None

        for prefix in self.exempt_prefixes:
            if prefix and request.path.startswith(prefix):
                return None

        login_url = resolve_url(settings.LOGIN_URL)
        return redirect(f"{login_url}?next={request.get_full_path()}")

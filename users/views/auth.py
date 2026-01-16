from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.utils.http import urlencode

from core import settings
from core.decorators import allow_anonymous
from core.views import UnitHubContextMixin


def get_enabled_auth_providers():
    providers = []

    if settings.AUTH_ENABLED_BUILTIN:
        providers.append("builtin")

    if settings.AUTH_ENABLED_DISCORD:
        providers.append("discord")

    if settings.AUTH_ENABLED_STEAM:
        providers.append("steam")

    return providers

@allow_anonymous
class CustomLoginView(UnitHubContextMixin, LoginView):
    template_name = 'login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.get_success_url())

        providers = get_enabled_auth_providers()

        if not settings.AUTH_ENABLED_BUILTIN and len(providers) == 1:
            provider = providers[0]

            next_url = request.GET.get("next")

            if provider == "discord":
                url = reverse("external_auth:discord_login")
            elif provider == "steam":
                url = reverse("external_auth:steam_login")
            else:
                raise ImproperlyConfigured("Invalid auth provider configuration")

            if next_url:
                url = f"{url}?{urlencode({'next': next_url})}"

            return redirect(url)

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy("dashboard-home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['builtin_login_enabled'] = settings.AUTH_ENABLED_BUILTIN
        context['discord_login_enabled'] = settings.AUTH_ENABLED_DISCORD
        context['steam_login_enabled'] = settings.AUTH_ENABLED_STEAM

        return context

def logout_view(request):
    logout(request)  # clears the session
    next_url = request.GET.get("next") or settings.LOGOUT_REDIRECT_URL
    return redirect(next_url)

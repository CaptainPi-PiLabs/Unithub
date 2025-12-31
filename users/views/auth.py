from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.http import urlencode

from core import settings
from core.views import UnitHubBaseView


class CustomLoginView(UnitHubBaseView, LoginView):
    template_name = 'login.html'

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect(self.get_success_url())

        if getattr(settings, 'DISCORD_CLIENT_ID', None):
            next_url = request.GET.get("next")
            redirect_url = reverse_lazy("external_auth:discord_login")
            if next_url:
                redirect_url = f"{redirect_url}?{urlencode({'next': next_url})}"
            return redirect(redirect_url)

        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy("dashboard-home")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['discord_login_enabled'] = bool(getattr(settings, 'DISCORD_CLIENT_ID', None))
        context['discord_auth_url'] = (
            f"https://discord.com/api/oauth2/authorize?"
            f"client_id={settings.DISCORD_CLIENT_ID}&"
            f"redirect_uri={settings.DISCORD_REDIRECT_URI}&"
            f"response_type=code&"
            f"scope=identify%20email%20guilds"
        ) if context['discord_login_enabled'] else None

        context['steam_login_enabled'] = bool(getattr(settings, 'STEAM_API_KEY', None))
        context['steam_auth_url'] = (
            f"https://steamcommunity.com/openid/login?"
            f"openid.ns=http://specs.openid.net/auth/2.0&"
            f"openid.mode=checkid_setup&"
            f"openid.return_to={settings.STEAM_REDIRECT_URI}&"
            f"openid.realm=https://yoursite.com&"
            f"openid.identity=http://specs.openid.net/auth/2.0/identifier_select&"
            f"openid.claimed_id=http://specs.openid.net/auth/2.0/identifier_select"
        ) if context['steam_login_enabled'] else None
        return context

def logout_view(request):
    logout(request)  # clears the session
    next_url = request.GET.get("next") or settings.LOGOUT_REDIRECT_URL
    return redirect(next_url)

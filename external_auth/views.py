from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import login
import requests
from django.shortcuts import redirect
from django.views import View

from external_auth.backends import ExternalAccountBackend
from external_auth.models import DiscordAccount
from core import settings


# Helper: exchange OAuth code for token
def get_discord_token(code):
    url = "https://discord.com/api/oauth2/token"
    data = {
        "client_id": settings.DISCORD_CLIENT_ID,
        "client_secret": settings.DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.DISCORD_REDIRECT_URI,
        "scope": "identify email guilds"
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    resp = requests.post(url, data=data, headers=headers)
    resp.raise_for_status()
    return resp.json()


# Helper: get user info from Discord
def get_discord_user(access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get("https://discord.com/api/users/@me", headers=headers)
    resp.raise_for_status()
    return resp.json()


# Create your views here.
class DiscordOAuthRedirectView(View):
    """
    Redirects user to Discord OAuth2 authorization page
    """
    def get(self, request):
        if not getattr(settings, "DISCORD_CLIENT_ID", None):
            return redirect("login")  # OAuth not configured

        params = {
            "client_id": settings.DISCORD_CLIENT_ID,
            "redirect_uri": settings.DISCORD_REDIRECT_URI,
            "response_type": "code",
            "scope": "identify"
        }
        url = f"https://discord.com/api/oauth2/authorize?{urlencode(params)}"
        return redirect(url)

class DiscordOAuthCallbackView(View):
    def get(self, request):
        code = request.GET.get("code")
        if not code:
            messages.error(request, "No code returned from Discord")
            return redirect("login")

        try:
            token_data = get_discord_token(code)
            discord_user = get_discord_user(token_data['access_token'])
        except Exception as e:
            messages.error(request, f"Discord authentication failed: {e}")
            return redirect("login")

        discord_id = discord_user['id']
        username = discord_user['username']
        avatar = discord_user.get("avatar")

        # Optional: construct avatar URL
        profile_url = (
            f"https://cdn.discordapp.com/avatars/{discord_id}/{avatar}.png"
            if avatar else None
        )

        discord_account, created = DiscordAccount.objects.get_or_create(
            external_id=discord_id,
            defaults={"username": username, "profile_url": profile_url},
        )

        if not created:
            updated = False
            if discord_account.username != username:
                discord_account.username = username
                updated = True
            if profile_url and discord_account.profile_url != profile_url:
                discord_account.profile_url = profile_url
                updated = True
            if updated:
                discord_account.save()

        if not discord_account.user:
            messages.info(request, "Your Discord account is not linked. Please contact an administrator.")
            return redirect("login")

        if not discord_account.user.is_active:
            messages.warning(request, "This account has been deactivated.")
            return redirect("login")

        backend = ExternalAccountBackend()
        user = backend.authenticate(request, external_account=discord_account)

        if not user:
            messages.error(request, "An error occured while trying to authenticate your Discord account.")
            return redirect("login")

        user.backend = "external_auth.backends.ExternalAccountBackend"
        login(request, user)

        next_url = request.GET.get("next") or settings.LOGIN_REDIRECT_URL
        return redirect(next_url)
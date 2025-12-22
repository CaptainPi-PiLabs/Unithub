from django.urls import path

from external_auth import views

app_name = "external_auth"

urlpatterns = [
    path("discord/", views.DiscordOAuthRedirectView.as_view(), name="discord_login"),
    path("discord/callback/", views.DiscordOAuthCallbackView.as_view(), name="discord_callback"),
]
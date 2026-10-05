from django.contrib import admin
from unfold.admin import ModelAdmin

from external_auth.models import DiscordAccount, SteamAccount


@admin.register(DiscordAccount)
class DiscordAccountAdmin(ModelAdmin):
    list_display = ('user', 'external_id', 'provider', 'username', 'profile_url')
    
@admin.register(SteamAccount)
class SteamAccountAdmin(ModelAdmin):
    list_display = ('user', 'external_id', 'provider', 'username', 'profile_url')
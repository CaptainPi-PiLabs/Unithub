from django.contrib import admin

from external_auth.models import DiscordAccount


@admin.register(DiscordAccount)
class DiscordAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'external_id', 'provider', 'username', 'profile_url')
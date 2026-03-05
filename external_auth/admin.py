from django.contrib import admin
from unfold.admin import ModelAdmin

from external_auth.models import DiscordAccount


@admin.register(DiscordAccount)
class DiscordAccountAdmin(ModelAdmin):
    list_display = ('user', 'external_id', 'provider', 'username', 'profile_url')
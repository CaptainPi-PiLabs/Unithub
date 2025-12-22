from django.contrib import admin

from external_auth.models import DiscordAccount


# Register your models here.
@admin.register(DiscordAccount)
class DiscordAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'external_id', 'provider', 'username', 'profile_url')
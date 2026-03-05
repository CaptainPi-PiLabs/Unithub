from django.contrib import admin
from unfold.admin import ModelAdmin

from timeline.models import TimelineEntry


# Register your models here.
@admin.register(TimelineEntry)
class TimelineEntryAdmin(ModelAdmin):
    list_display = ('user', 'section', 'event_type', 'snapshot_name', 'timestamp')
    list_filter = ('section',)
    search_fields = ['user__display_name']
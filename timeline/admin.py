from django.contrib import admin

from timeline.models import TimelineTypes, TimelineEntry


# Register your models here.
@admin.register(TimelineEntry)
class TimelineEntryAdmin(admin.ModelAdmin):
    list_display = ('user', 'section', 'event_type', 'snapshot_name', 'timestamp')
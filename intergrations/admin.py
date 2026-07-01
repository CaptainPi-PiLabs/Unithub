import json

from django.contrib import admin
from django.utils.safestring import mark_safe

from .models import IntegrationEvent


@admin.register(IntegrationEvent)
class IntegrationEventAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "event_type",
        "status",
        "attempts",
        "created",
        "updated",
    )

    list_filter = (
        "status",
        "event_type",
        "created",
    )

    search_fields = (
        "id",
        "event_type",
    )

    readonly_fields = (
        "created",
        "updated",
        "formatted_payload",
        "error",
    )

    exclude = ("payload",)

    ordering = ("-created",)

    @admin.display(description="Payload")
    def formatted_payload(self, obj):
        return mark_safe(f"<pre>{json.dumps(obj.payload, indent=2)}</pre>")
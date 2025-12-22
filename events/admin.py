from django.contrib import admin

from events.models import Campaign, EventGroup, EventRole, EventAssignment, Event


# ──────────────────────────────────────────────
# Campaign Admin
# ──────────────────────────────────────────────

@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ("name", "start_date", "end_date")
    search_fields = ("name", "description")
    list_filter = ("start_date", "end_date")


# ──────────────────────────────────────────────
# Event Inline Admin
# ──────────────────────────────────────────────

class EventGroupInline(admin.TabularInline):
    model = EventGroup
    extra = 1
    autocomplete_fields = ("orbat_section",)


class EventRoleInline(admin.TabularInline):
    model = EventRole
    extra = 1
    autocomplete_fields = ("user",)


class EventAssignmentInline(admin.TabularInline):
    model = EventAssignment
    extra = 1
    autocomplete_fields = ("user", "event_group", "assigned_by")
    fields = (
        "user",
        "status",
        "event_group",
        "role",
        "colour",
        "assigned_by",
        "assigned_at",
        "order",
    )
    readonly_fields = ("assigned_at",)

# ──────────────────────────────────────────────
# Event Admin
# ──────────────────────────────────────────────

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("name", "date", "start_time", "type", "campaign")
    search_fields = ("name", "description")
    list_filter = ("type", "campaign", "date")
    ordering = ("-date", "start_time")

    inlines = [
        EventGroupInline,
        EventRoleInline,
        EventAssignmentInline,
    ]


# ──────────────────────────────────────────────
# EventGroup Admin
# ──────────────────────────────────────────────

@admin.register(EventGroup)
class EventGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "event", "orbat_section")
    search_fields = ("name",)
    list_filter = ("event",)


# ──────────────────────────────────────────────
# EventAssignment Admin
# ──────────────────────────────────────────────

@admin.register(EventAssignment)
class EventAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "event",
        "user",
        "status",
        "event_group",
        "role",
        "colour",
        "order",
    )

    list_filter = ("status", "colour", "event", "event_group")
    search_fields = ("user__username", "role")

    autocomplete_fields = ("user", "event_group", "assigned_by", "event")
    ordering = ("event", "order")


# ──────────────────────────────────────────────
# EventRole Admin
# ──────────────────────────────────────────────

@admin.register(EventRole)
class EventRoleAdmin(admin.ModelAdmin):
    list_display = ("event", "user", "role")
    list_filter = ("role", "event")
    search_fields = ("user__username",)
    autocomplete_fields = ("user", "event")
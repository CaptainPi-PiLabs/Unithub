from common.views import UnitHubListView
from orbat.views.mixins import ORBATContextMixin
from timeline.builder_display import build_timeline_display_entries
from timeline.builders import get_orbat_timeline, group_timeline_entries
from timeline.service import TimelineService
from timeline.utils import (
    get_active_context,
    get_start_date_query,
)


class ORBATTimelineView(ORBATContextMixin, UnitHubListView):
    template_name = "orbat/timeline.html"

    def get_queryset(self):
        request = self.request
        active = get_active_context(request)

        user = active.get("active_timeline_user")
        section = active.get("active_timeline_section")
        start_date = get_start_date_query(
            None,
            active.get("active_timeline_range")
        )

        return TimelineService.get_orbat_timeline(
            user=user,
            section=section,
            start_date=start_date,
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # active = get_active_context(self.request)

        events = get_orbat_timeline()

        # Presentation projection
        display_entries = build_timeline_display_entries(events)

        context["timeline_entries"] = group_timeline_entries(display_entries)

        # UI state
        # context.update(build_timeline_context(events))
        # context.update(active)

        return context
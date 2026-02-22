from common.views import UnitHubListView
from orbat.views.mixins import ORBATContextMixin
from timeline.models import TimelineEntry
from timeline.utils import (
    build_timeline_context,
    group_timeline_entries,
    get_active_context,
    get_user_query,
    get_section_query,
    get_start_date_query,
)


class ORBATTimelineView(ORBATContextMixin, UnitHubListView):
    template_name = "orbat/timeline.html"
    model = TimelineEntry
    context_object_name = "timeline_qs"
    paginate_by = None  # grouping makes pagination messy

    def get_queryset(self):
        request = self.request

        # Base queryset
        qs = TimelineEntry.objects.select_related("user", "section")

        # Active filters
        active = get_active_context(request)

        # User filter
        user_qs = get_user_query(None, active["active_timeline_user"])
        qs = qs.filter(user__in=user_qs)

        # Section filter
        section = get_section_query(None, active["active_timeline_section"])
        if section:
            qs = qs.filter(section=section)

        # Date range filter
        start_date = get_start_date_query(None, active["active_timeline_range"])
        if start_date:
            qs = qs.filter(timestamp__gte=start_date)

        return qs.order_by("-timestamp")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        timeline_qs = context["timeline_qs"]

        # Build filter dropdown context
        context.update(build_timeline_context(timeline_qs))

        # Active state
        context.update(get_active_context(self.request))

        # Group entries by date
        context["entries"] = group_timeline_entries(timeline_qs)

        context["breadcrumbs"] = [
            {"name": "ORBAT", "url": "/orbat/"},
            {"name": "Timeline", "url": None},
        ]

        return context
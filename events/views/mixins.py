from django.conf import settings

from core.exceptions import WIPFeatureError


class EventContextMixin:
    title = "Events"

    def dispatch(self, request, *args, **kwargs):
        if not getattr(settings, "ENABLE_EVENTS", False):
            raise WIPFeatureError
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        is_manager = False

        if user.is_authenticated:
            is_manager = user.is_staff

        context["show_management"] = is_manager
        context["title"] = self.title

        context["sidebar"] = [
            {"name": "Upcoming", "path": "/events/"},
            {"name": "Calendar", "path": "/events/calendar/"},
            {"name": "Campaigns", "path": "/events/campaigns/"},
            {"name": "Trainings", "path": "/events/"},
            {"name": "Side OPs", "path": "/events/"},
        ]

        if context["show_management"]:
            context["sidebar"].append({"name": "Management", "path": "/events/manage/"})

        return context
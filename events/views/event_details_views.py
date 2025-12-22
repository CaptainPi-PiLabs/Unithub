from django.core.exceptions import PermissionDenied

from events.models import Campaign, Event
from events.views import EventBaseView


class CampaignDetailView(EventBaseView):
    template_name = "campaign_detail.html"
    title = "Campaign"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        campaign = Campaign.objects.get(pk=kwargs["pk"])

        context["campaign"] = campaign
        context["events"] = campaign.events
        context["page_title"] = campaign.name

        return context

class EventDetailView(EventBaseView):
    template_name = "event_detail.html"
    title = "Event"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        event = Event.objects.select_related("campaign").get(pk=kwargs["pk"])
        context["event"] = event
        context["page_title"] = event.name

        context["groups"] = event.groups.all().order_by("order")
        context["assignments"] = (
            event.assignments.select_related("users", "event_group").order_by("event_group__order", "order")
        )

        return context

class EventManageView(EventDetailView):
    template_name = "event_manage.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied()
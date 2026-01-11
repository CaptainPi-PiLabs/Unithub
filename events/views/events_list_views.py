from datetime import datetime

from dateutil.relativedelta import relativedelta
from django.utils import timezone

from events.models import Event, Campaign
from events.views import EventBaseView


class EventListView(EventBaseView):
    template_name = "events_upcoming.html"
    title = "Upcoming Events"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["breadcrumbs"] = [
            {"name": "Events", "url": None},
        ]

        context["upcoming_events"] = (
            Event.objects.filter(date__gte=timezone.now()).order_by("date")[:10]
        )

        return context

class EventCalendarView(EventBaseView):
    template_name = "event_calendar.html"
    title = "Event Calendar"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["breadcrumbs"] = [
            {"name": "Events", "url": "/events/"},
            {"name": "Calendar", "url": None},
        ]

        # extract ?year=YYYY&month=MM
        year = int(self.request.GET.get("year", timezone.now().year))
        month = int(self.request.GET.get("month", timezone.now().month))

        start = datetime(year, month, 1)
        end = start + relativedelta(months=1)

        events = (
            Event.objects.filter(date__gte=start, date__lt=end)
            .order_by("date")
        )

        context.update({
            "selected_year": year,
            "selected_month": month,
            "events": events,
            "current_month_name": start.strftime("%B"),
            "prev_month": (start - relativedelta(months=1)),
            "next_month": (start + relativedelta(months=1)),
        })

        return context

class CampaignListView(EventBaseView):
    template_name = "campaign_list.html"
    title = "Campaigns"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["breadcrumbs"] = [
            {"name": "Events", "url": "/events/"},
            {"name": "Campaigns", "url": None},
        ]

        context["campaigns"] = Campaign.objects.all()

        return context
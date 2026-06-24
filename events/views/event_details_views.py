from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse
from django.utils import timezone

from common.views import UnitHubDetailView, UnitHubUpdateView
from events.models import Campaign, Event, EventGroup
from events.views import EventContextMixin
from training.models import UserQualification

EVENT_TEMPLATES = {
    "TR": "events/training_event_detail.html",
    "OP": "events/operation_event_detail.html",
}

class CampaignDetailView(EventContextMixin, UnitHubDetailView):
    model = Event
    title = "Campaign"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        campaign = Campaign.objects.get(pk=kwargs["pk"])

        context["campaign"] = campaign
        context["events"] = campaign.events
        context["page_title"] = campaign.name

        return context

class EventDetailView(EventContextMixin, UnitHubDetailView):
    model = Event
    template_name = "events/event_detail.html"
    title = "Event"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .prefetch_related(
                "roles__user",
                "assignments__user",
                "groups",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["page_title"] = self.object.name
        context["today"] = timezone.now().date()
        context["exit_url"] = self.get_exit_url()

        return context

    def get_template_names(self):
        obj = getattr(self, "object", None) or self.get_object()
        return [
            EVENT_TEMPLATES.get(obj.type, self.template_name)
        ]

    def get_exit_url(self):
        if self.object.qualification:
            if self.object.qualification.is_bct:
                return reverse("orbat_applications_onboarding_list")
            return reverse("training_matrix")
        return reverse("event_list")

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()

        action = request.POST.get("action")

        if action == "certify_attendees":
            return self._certify_attendees(request)

        return super().post(request, *args, **kwargs)

    def _certify_attendees(self, request):
        qualification = self.object.qualification

        if not qualification:
            messages.error(request, "This event is not linked to a qualification.")
            return redirect(request.path)

        trainee_group = self.object.groups.filter(
            name=EventGroup.TRAINEES
        ).first()

        if not trainee_group:
            messages.error(request, "No trainee group found.")
            return redirect(request.path)

        assignments = self.object.assignments.filter(
            event_group=trainee_group
        ).select_related("user")

        created = 0

        for assignment in assignments:
            _, was_created = UserQualification.objects.get_or_create(
                user=assignment.user,
                qualification=qualification,
                defaults={
                    "granted_by": request.user,
                }
            )

            if was_created:
                created += 1

        self.object.status = "COMPLETED"
        self.object.save(update_fields=["status"])

        messages.success(
            request,
            f"Certified {created} attendee{'s' if created != 1 else ''}."
        )

        return redirect(self.get_exit_url())

class EventManageView(EventContextMixin, UnitHubUpdateView):
    template_name = "events/event_manage.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            raise PermissionDenied()

class TrainingEventDetailView(EventContextMixin, UnitHubDetailView):
    template_name = "events/training_event_detail.html"

    def get_queryset(self):
        return super().get_queryset().filter(type="TR")


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["page_title"] = self.object.name

        return context
from django.shortcuts import get_object_or_404
from django.utils import timezone

from common.views import UnitHubListView, UnitHubDetailView
from permissions.engine import has_training_permission
from training.enums import TrainingActions
from training.models import Qualification, QualificationCriterion, QualificationTrainer
from training.views.mixins import TrainingContextMixin


class QualificationsListView(TrainingContextMixin, UnitHubListView):
    template_name = "training/qualifications_list.html"

    def get_queryset(self):
        show_archived = self.request.GET.get("archived") == "1"
        if show_archived:
            return Qualification.objects.all()
        return Qualification.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_create_qualifications"] = has_training_permission(self.request.user, TrainingActions.CREATE_QUALIFICATION)
        context["show_archived"] = self.request.GET.get("archived") == "1"

        context["breadcrumbs"] = [
            {"name": "Training", "url": '/training'},
            {"name": "Qualifications", "url": None}
        ]

        return context

class QualificationDetailView(TrainingContextMixin, UnitHubDetailView):
    template_name = "training/qualification_detail.html"

    def get_object(self):
        pk = self.kwargs["qual_id"]
        return get_object_or_404(Qualification, pk=pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qualification = self.object
        user = self.request.user

        # --------------------
        # Active tab
        # --------------------
        allowed_tabs = {"criteria", "trainers", "events"}
        requested_tab = self.request.GET.get("tab", "criteria")
        context["active_tab"] = requested_tab if requested_tab in allowed_tabs else "criteria"

        # --------------------
        # Permissions
        # --------------------
        context["can_edit"] = has_training_permission(
            user,
            TrainingActions.MODIFY_QUALIFICATION,
            qualification,
        )

        context["can_manage_trainers"] = has_training_permission(
            user,
            TrainingActions.MANAGE_TRAINERS,
            qualification,
        )

        context["can_create_event"] = has_training_permission(
            user,
            TrainingActions.GRANT_CERTIFICATE,
            qualification,
        )

        # --------------------
        # Criteria
        # --------------------
        context["criteria"] = (
            QualificationCriterion.objects
            .filter(qualification=qualification)
            .order_by("order")
        )

        context["criteria_json"] = [
            {
                "id": criterion.id,
                "name": criterion.name,
                "description": criterion.description,
            }
            for criterion in context["criteria"]
        ]

        # --------------------
        # Trainers
        # --------------------
        context["trainers"] = (
            QualificationTrainer.objects
            .filter(qualification=qualification)
            .select_related("user")
            .order_by("user__display_name")
        )

        # --------------------
        # Events
        # --------------------
        now = timezone.now()
        # context["events"] = (
        #    TrainingEvent.objects
        #    .filter(qualification=qualification)
        #    .order_by("-start_time")
        # )

        return context

from django.shortcuts import get_object_or_404
from django.utils import timezone

from common.views import UnitHubListView, UnitHubDetailView
from permissions.engine import has_training_permission
from training.enums import TrainingActions
from training.models import Qualification, QualificationCriterion, QualificationTrainer
from training.views.mixins import TrainingContextMixin


LIST_ACTION_MAP = {
    "create_qualification": {
        "perm": TrainingActions.CREATE_QUALIFICATION,
        "handler": "_create_qualification",
    },
    "move_qualification": {
        "perm": TrainingActions.MODIFY_QUALIFICATION,
        "handler": "_move_qualification",
    }
}

DETAIL_ACTION_MAP = {
    "save_qualification": {
        "perm": TrainingActions.MODIFY_QUALIFICATION,
        "handler": "_save_qualification",
    },
    "delete_qualification": {
        "perm": TrainingActions.REMOVE_QUALIFICATION,
        "handler": "_delete_qualification",
    },
    "save_criterion": {
        "perm": TrainingActions.MODIFY_CRITERIA,
        "handler": "_save_criterion",
    },
    "delete_criterion": {
        "perm": TrainingActions.REMOVE_CRITERIA,
        "handler": "_delete_criterion",
    },
    "move_criterion": {
        "perm": TrainingActions.MODIFY_CRITERIA,
        "handler": "_move_criterion",
    },
    "save_trainer": {
        "perm": TrainingActions.MANAGE_TRAINERS,
        "handler": "_save_trainer",
    },
    "remove_trainer": {
        "perm": TrainingActions.MANAGE_TRAINERS,
        "handler": "_remove_trainer",
    },
}

ROLE_HIERARCHY = {
    "Trainer": 1,
    "Senior Trainer": 2,
    "Manager": 3,
}


class QualificationsListView(TrainingContextMixin, UnitHubListView):
    template_name = "training/qualifications_list.html"
    breadcrumbs = [
        ("Training", "/training/"),
        ("Qualifications", None),
    ]

    def get_queryset(self):
        show_archived = self.request.GET.get("archived") == "1"
        if show_archived:
            return Qualification.objects.all()
        return Qualification.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["can_create_qualifications"] = has_training_permission(self.request.user, TrainingActions.CREATE_QUALIFICATION)
        context["show_archived"] = self.request.GET.get("archived") == "1"

        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        config = LIST_ACTION_MAP.get(action)

        if not config:
            raise PermissionDenied()

        if not has_training_permission(request.user, config["perm"]):
            raise PermissionDenied()

        # Execute handler
        handler = getattr(self, config["handler"])
        handler(request)

        return redirect(self.request.path)

    def _create_qualification(self, request):
        name = request.POST.get("name")
        description = request.POST.get("description")
        if not name:
            raise BadRequest()
        try:
            Qualification.objects.create(name=name, description=description)
        except IntegrityError:
            raise BadRequest()

    def _move_qualification(self, request):
        qualification = Qualification.objects.get(pk=request.POST.get("pk"))
        position = request.POST.get("position")
        qualification.move_to(int(position))

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

from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from core.views import UnitHubListView, UnitHubUpdateView, UnitHubCreateView, UnitHubDetailView
from permissions.engine import has_training_permission
from training.enums import TrainingActions
from training.forms import QualificationCriterionForm, QualificationForm
from training.models import Qualification, QualificationCriterion, QualificationTrainer
from training.views import TrainingContextMixin


class QualificationsListView(TrainingContextMixin, UnitHubListView):
    template_name = "qualifications_list.html"

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
    template_name = "qualification_detail.html"

    def get_object(self):
        pk = self.kwargs["pk"]
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

        # --------------------
        # Breadcrumbs
        # --------------------
        context["breadcrumbs"] = [
            {"name": "Training", "url": "/training/"},
            {"name": "Qualifications", "url": "/training/qualifications/"},
            {"name": qualification.name, "url": None},
        ]

        return context

class TrainingManagementCreateView(TrainingContextMixin, UnitHubCreateView):
    model = Qualification
    form_class = QualificationForm
    template_name = "training_qualification_create.html"

    def get_success_url(self):
        return reverse(
            "qualification_detail",
            kwargs={"pk": self.object.pk},
        )

    def dispatch(self, request, *args, **kwargs):
        if not has_training_permission(self.request.user, TrainingActions.CREATE_QUALIFICATION):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        self.add_message("Qualification created successfully")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page_title"] = "New Qualification"
        context["breadcrumbs"] = [
            {"name": "Training", "url": "/training"},
            {"name": "Qualifications", "url": "/training/qualifications/"},
            {"name": "New Qualification", "url": None},
        ]
        return context

class TrainingManagementEditView(TrainingContextMixin, UnitHubUpdateView):
    template_name = "training_management_edit.html"

    def get_object(self):
        pk = self.kwargs["pk"]
        qualification = get_object_or_404(Qualification, pk=pk)
        if not has_training_permission(self.request.user, TrainingActions.MODIFY_QUALIFICATION, qualification):
            raise PermissionDenied
        return qualification

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qualification = self.get_object()

        CriterionFormset = inlineformset_factory(
            Qualification, QualificationCriterion,
            form=QualificationCriterionForm, extra=1, can_delete=True
        )

        if self.request.method == "POST":
            context["form"] = QualificationForm(self.request.POST, instance=qualification)
            context["formset"] = CriterionFormset(self.request.POST, instance=qualification)
        else:
            context["form"] = QualificationForm(instance=qualification)
            context["formset"] = CriterionFormset(instance=qualification)

        context["qualification"] = qualification
        context["page_title"] = f"Edit {qualification.name}"
        return context

    def post(self, request, *args, **kwargs):
        qualification = self.get_object()
        CriterionFormset = inlineformset_factory(
            Qualification, QualificationCriterion,
            form=QualificationCriterionForm, extra=1, can_delete=True
        )
        form = QualificationForm(request.POST, instance=qualification)
        formset = CriterionFormset(request.POST, instance=qualification)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect("training_management_detail", pk=qualification.pk)

        context = self.get_context_data()
        context["form"] = form
        context["formset"] = formset
        return self.render_to_response(context)
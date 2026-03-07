from django.contrib.auth import get_user_model

from common.views import UnitHubTemplateView
from orbat.models.sections import Section, SectionSlotAssignment
from training.models import Qualification, UserQualification
from training.views.mixins import TrainingContextMixin


class TrainingMatrixView(TrainingContextMixin, UnitHubTemplateView):
    template_name = "training/training_matrix.html"
    breadcrumbs = [
        ("Training", "/training/"),
        ("Matrix", None)
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["page_title"] = "Matrix"

        section_filter = self.request.GET.get("section")
        base_users, current_section_id = self.get_users_for_section(section_filter)
        context["current_section_id"] = current_section_id

        # Map user_id -> list of qualification IDs
        user_qual_map = self.build_user_qualification_map(base_users)
        context["users"] = [
            {
                "id": str(user.id),
                "display_name": user.display_name,
                "qualifications": user_qual_map.get(str(user.id), []),
            }
            for user in base_users
        ]

        context["sections"] = Section.objects.all().order_by("name")
        context["qualifications"] = Qualification.objects.filter(is_active=True).order_by("order")

        return context

    def get_users_for_section(self, section_filter):
        """
        Returns (QuerySet[User], current_section_id)
        """
        User = get_user_model()
        if not section_filter:
            return User.objects.filter(is_active=True), None

        if section_filter == "unassigned":
            assigned_user_ids = SectionSlotAssignment.objects.filter(
                end_date__isnull=True
            ).values_list("user_id", flat=True)
            return User.objects.filter(is_active=True).exclude(id__in=assigned_user_ids), "unassigned"

        # specific section
        assigned_user_ids = SectionSlotAssignment.objects.filter(
            slot__section_id=section_filter, end_date__isnull=True
        ).values_list("user_id", flat=True)
        return User.objects.filter(id__in=assigned_user_ids), int(section_filter)

    def build_user_qualification_map(self, users):
        """
        Returns {user_id: [qualification_ids]} for passed qualifications
        """
        user_ids = [user.id for user in users]
        quals = UserQualification.objects.filter(
            user_id__in=user_ids
        ).values("user_id", "qualification_id")

        mapping = {}
        for uq in quals:
            mapping.setdefault(str(uq["user_id"]), []).append(uq["qualification_id"])
        return mapping
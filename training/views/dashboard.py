from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from common.views import UnitHubTemplateView
from users.views import ProfileContextMixin
from .mixins import TrainingContextMixin
from ..models import Qualification, QualificationTrainer, UserQualification


class TrainingHomeView(TrainingContextMixin, UnitHubTemplateView):
    template_name = "training/training_home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["page_title"] = "Home"

        context["breadcrumbs"] = [
            {"name": "Training", "url": None},
        ]

        return context

class UserTrainingView(ProfileContextMixin, UnitHubTemplateView):
    template_name = "training/training_user_overview.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = kwargs.get("user_id")
        profile_user = get_object_or_404(get_user_model(), pk=user_id)
        request_user = self.request.user

        # Fetch all active qualifications, ordered
        qualifications = Qualification.objects.filter(is_active=True).order_by("order")

        # Prefetch user qualifications for efficiency
        user_quals = UserQualification.objects.filter(user=profile_user).select_related('qualification')
        user_qual_map = {uq.qualification_id: uq for uq in user_quals}

        training_data = []

        for qual in qualifications:
            user_qual = user_qual_map.get(qual.id)
            passed = user_qual.latest_passed is not None if user_qual else False
            first_passed = user_qual.date_awarded if user_qual else None
            latest_passed = user_qual.latest_passed if user_qual else None

            # Get criteria for this qualification
            criteria_qs = qual.criteria.all().order_by("order")
            criteria_list = []
            for crit in criteria_qs:
                crit_passed = False
                if user_qual:
                    # Here you can add a model UserQualificationCriterion if you track individual criterion passes
                    # For now we assume criterion is passed if qualification is passed
                    crit_passed = passed
                criteria_list.append({
                    "id": crit.id,
                    "name": crit.name,
                    "order": crit.order,
                    "passed": crit_passed,
                })

            # Determine if current user can manage this qualification
            can_manage = False
            if request_user.is_authenticated:
                is_trainer = QualificationTrainer.objects.filter(
                    user=request_user,
                    qualification=qual
                ).exists()
                can_manage = is_trainer or request_user.is_staff

            training_data.append({
                "id": qual.id,
                "name": qual.name,
                "description": qual.description,
                "passed": passed,
                "first_passed": first_passed,
                "latest_passed": latest_passed,
                "criteria": criteria_list,
                "can_manage_cert": can_manage,
            })

        context["training_data"] = training_data
        context["profile_user"] = profile_user
        return context
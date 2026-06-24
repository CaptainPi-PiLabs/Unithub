import json

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils import timezone
from rest_framework.utils import breadcrumbs

from common.views import UnitHubDetailView
from permissions.engine import has_training_permission
from training.enums import TrainingActions
from training.models import Qualification, UserQualification
from training.views.mixins import TrainingContextMixin
from users.models import UnitMembership


class TrainingQualificationGrantView(TrainingContextMixin, UnitHubDetailView):
    template_name = "training/qualification_grant.html"

    def get_object(self):
        pk = self.kwargs["qual_id"]
        return get_object_or_404(Qualification, pk=pk)

    def dispatch(self, request, *args, **kwargs):
        qualification = self.get_object()
        if not has_training_permission(
            request.user,
            TrainingActions.GRANT_CERTIFICATE,
            qualification,
        ):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_breadcrumbs(self):
        qualification = self.get_object()
        return self.build_breadcrumbs(
            ("Training", "/training/"),
            ("Qualification", "/training/qualifications/"),
            (qualification.name, reverse("training_qualification_detail", kwargs={"qual_id": qualification.id})),
            ("Grant Certificate", None),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qualification = self.get_object()

        context["qualification"] = qualification
        context["trainer"] = self.request.user.display_name

        members_json = []

        for member in UnitMembership.objects.filter(end_date__isnull=True).select_related("user"):
            members_json.append({
                "id": member.user.id,
                "name": member.user.display_name or member.user.username
            })

        context["active_members_json"] = members_json

        context["page_title"] = "Grant Certificate"
        return context

    def post(self, request, *args, **kwargs):
        qualification = self.get_object()

        try:
            member_ids_json = request.POST.get("members", "[]")
            member_ids = json.loads(member_ids_json)

        except Exception:
            messages.error(request, "Invalid request body")
            return redirect(request.path)

        if not member_ids:
            messages.error(request, "No members selected")
            return redirect(request.path)

        today = timezone.now().date()

        try:
            with transaction.atomic():
                for member_id in member_ids:
                    obj, created = UserQualification.objects.get_or_create(
                        user_id=member_id,
                        qualification=qualification,
                        defaults={
                            "date_awarded": today,
                            "latest_passed": today,
                            "granted_by": request.user,
                        }
                    )

                    if not created:
                        obj.latest_passed = today
                        obj.granted_by = request.user
                        obj.save(update_fields=["latest_passed", "granted_by"])

            messages.success(
                request,
                f"Successfully granted {qualification.name} to {len(member_ids)} members.")
            return redirect("training_qualification_detail", qualification.id)

        except Exception as e:
            messages.error(request, "Failed to grant qualification")
            return redirect(request.path)
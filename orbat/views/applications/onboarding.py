import re

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html

from common.views import UnitHubTemplateView
from orbat.enums import OrbatActions
from orbat.models.unit import UnitApplication
from orbat.views.mixins import ORBATContextMixin
from permissions.engine import has_orbat_permission
from training.models import Qualification, UserQualification
from users.models import UserStatus, CustomUserManager

ACTION_MAP = {
    "save_user": {
        "perm": OrbatActions.MANAGE_UNIT_APPLICATIONS,
        "handler": "_save_user",
    },
    "delete_user": {
        "perm": OrbatActions.DENY_UNIT_APPLICATIONS,
        "handler": "_delete_user",
    },
    "save_application": {
        "perm": OrbatActions.MANAGE_UNIT_APPLICATIONS,
        "handler": "_save_application",
    },
    "approve_application": {
        "perm": OrbatActions.MANAGE_UNIT_APPLICATIONS,
        "handler": "_approve",
    },
    "deny_application": {
        "perm": OrbatActions.DENY_UNIT_APPLICATIONS,
        "handler": "_deny",
    }
}

User = get_user_model()


class UnitApplicationOnboarding(ORBATContextMixin, UnitHubTemplateView):
    template_name = 'orbat/applications/onboarding.html'

    breadcrumbs = [
        ("Applications", "orbat_applications"),
        ("Onboarding", None)
    ]

    def dispatch(self, request, *args, **kwargs):
        if not has_orbat_permission(self.request.user, OrbatActions.VIEW_UNIT_APPLICATIONS):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def _get_application(self):
        pk = self.kwargs.get("pk")
        if not pk:
            return None
        try:
            return UnitApplication.objects.get(pk=pk, closed=False)
        except UnitApplication.DoesNotExist:
            self.add_message("Application does not exist.", level=messages.ERROR)
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        app = self._get_application()
        bct = Qualification.get_bct()

        if app:
            context["focused_application"] = app
            other_qs = (
                UnitApplication.objects.filter(closed=False)
                .order_by("date")[:10]
            )

            context["passed_bct"] = False
            if app.user:
                context["passed_bct"] = UserQualification.objects.filter(
                    user=app.user,
                    qualification__is_bct=True,
                ).exists()

            context["application_json"] = {
                "id": app.pk,
                "user_id": str(app.user.id) if app.user else None,
                "name": app.user.display_name if app.user else "",
                "teamspeak_id": app.teamspeak_id,
                "over_18": app.over_18,
            }
        else:
            other_qs = UnitApplication.objects.filter(closed=False).order_by("date")[:10]
        context["other_applications"] = other_qs

        user = self.request.user
        context["can_manage"] = has_orbat_permission(user, OrbatActions.MANAGE_UNIT_APPLICATIONS)
        context["can_deny"] = has_orbat_permission(user, OrbatActions.DENY_UNIT_APPLICATIONS)
        context["can_approve"] = app is not None and app.user is not None and has_orbat_permission(user, OrbatActions.APPROVE_UNIT_APPLICATIONS)

        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        config = ACTION_MAP.get(action)

        if not config:
            raise PermissionDenied()

        app = self._get_application()
        if not app:
            raise PermissionDenied("No application selected")

        if not has_orbat_permission(request.user, config["perm"]):
            raise PermissionDenied()

        # Execute handler
        handler = getattr(self, config["handler"])
        response = handler(request, app)

        if response is not None:
            return response

        return redirect(self.request.path)

    def _save_user(self, request, app, *args, **kwargs):
        name = request.POST.get("name", "").strip()

        if not name:
            self.add_message("Please enter a name.", level=messages.ERROR)
            return

        username = User.normalize_username(name)

        # Check for conflicting users (exclude current user if updating)
        check_user = User.objects.filter(
            username=username
        ).exclude(pk=getattr(app.user, "pk", None)).first()

        if not app.user: # Create a new user
            if check_user:
                self.add_message("This name conflicts with another user", level=messages.ERROR)
                return

            user = User.objects.create(
                display_name=name,
                username=username,
                status=UserStatus.APPLICANT,
            )
            app.user = user
            app.external_account.user = user
            app.external_account.save()
            app.save()
        else:
            if check_user and check_user != app.user:
                self.add_message("This name conflicts with another user", level=messages.ERROR)
                return

            updated_fields = []
            if app.user.display_name != name:
                app.user.display_name = name
                updated_fields.append("display_name")
            if app.user.username != username:
                app.user.username = username
                updated_fields.append("username")
            if updated_fields:
                app.user.save(update_fields=updated_fields)

        target_name = app.user.display_name if app.user else app.external_account.username

        self.add_message(
            f"Application for {target_name} updated.",
            level=messages.INFO
        )

    def _delete_user(self, request, app, *args, **kwargs):
        if not app.user:
            self.add_message("User does not exist.", level=messages.ERROR)
            return
        if app.user.status != UserStatus.APPLICANT: # Safety protection
            self.add_message("Only applicant accounts can be deleted.", level=messages.ERROR)
            return
        user = app.user
        display_name = user.display_name
        user.delete()
        self.add_message(f"User {display_name} deleted.", level=messages.SUCCESS)

    def _save_application(self, request, app, *args, **kwargs):
        app.teamspeak_id = request.POST.get("teamspeak_id") or None
        app.over_18 = request.POST.get("over_18") == "true"
        app.save()
        self.add_message(f"Application updated", level=messages.SUCCESS)

    def _approve(self, request, app, *args, **kwargs):
        if not app.user:
            self.add_message("Cannot approve an application without a user.", level=messages.ERROR)
            return None

        try:
            app.approve(actioned_by=self.request.user)
        except ValidationError as e:
            self.add_message(e.message, level=messages.ERROR)
            return None

        profile_url = reverse("user_profile", kwargs={"user_id": app.user.pk})
        self.add_message(
            format_html(
                "Application approved. User profile: <a href='{}'>{}</a>",
                profile_url,
                app.user.display_name,
            ),
            level=messages.SUCCESS,
        )
        return redirect("orbat_applications_onboarding_list")

    def _deny(self, request, app, *args, **kwargs):

        reason = request.POST.get("reason", "").strip()
        try:
            app.deny(actioned_by=self.request.user, reason=reason)
        except ValidationError as e:
            self.add_message(e.message, level=messages.ERROR)
            return None

        target_name = (
            app.user.display_name
            if app.user
            else app.external_account.username
        )

        if app.user:
            self.add_message(
                format_html(
                    "Application denied. User profile: <a href='{}'>{}</a>",
                    reverse("user_profile", kwargs={"user_id": app.user.pk}),
                    target_name,
                ),
                level=messages.WARNING,
            )
        else:
            self.add_message(
                f"Application denied for {target_name}.",
                level=messages.WARNING,
            )

        return redirect("orbat_applications_onboarding_list")
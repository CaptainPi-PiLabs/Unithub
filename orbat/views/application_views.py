from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError, PermissionDenied
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.utils.html import format_html
from django.views import View

from common.views import UnitHubTemplateView
from orbat.enums import OrbatActions
from orbat.models.sections import SectionApplication
from orbat.models.unit import UnitApplication
from orbat.selectors import get_section_slot
from orbat.views.mixins import ORBATContextMixin
from permissions.engine import has_orbat_permission
from users.models import UserStatus


class ORBATApplicationLOA(View):
    template_name = 'orbat/section_detail.html'

class ORBATApplicationJoin(View):
    template_name = 'orbat/section_detail.html'

class ORBATApplicationOverview(ORBATContextMixin, UnitHubTemplateView):
    template_name = 'orbat/applications.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if has_orbat_permission(self.request.user, OrbatActions.MANAGE_UNIT_APPLICATIONS):
            context['unit_application_perms'] = True
            context['unit_applications'] = UnitApplication.objects.filter(processed_date=None).order_by('date')

        managed_section = None
        slot = get_section_slot(self.request.user)
        if slot and slot.is_leader:
            managed_section = slot.section

        if self.request.user.is_staff or managed_section:
            if not managed_section:
                section_applications = SectionApplication.objects.filter(processed_date=None).order_by('date')
            else:
                section_applications = SectionApplication.objects.filter(processed_date=None, section_slot__section=managed_section).order_by('date')
            context['section_application_perms'] = True
            context['section_applications'] = section_applications

        return context

class UnitApplicationOnboarding(ORBATContextMixin, UnitHubTemplateView):
    template_name = 'orbat/applications_onboarding.html'

    def dispatch(self, request, *args, **kwargs):
        if not has_orbat_permission(self.request.user, OrbatActions.VIEW_UNIT_APPLICATIONS):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def _get_application(self):
        pk = self.kwargs.get("pk")
        if not pk:
            self.add_message("No application found.", level=messages.ERROR)
            return None
        try:
            return UnitApplication.objects.get(pk=pk, closed=False)
        except UnitApplication.DoesNotExist:
            self.add_message("Application does not exist.", level=messages.ERROR)
            return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        app = self._get_application()
        if app:
            context["focused_application"] = app
            other_qs = (
                UnitApplication.objects.filter(closed=False)
                .order_by("date")[:10]
            )

            context["slide_json"] = {
                "id": app.pk,
                "user_id": str(app.user.id) if app.user else None,
                "username": app.user.username if app.user else "",
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


class UnitApplicationUserManager(UnitApplicationOnboarding):
    def dispatch(self, request, *args, **kwargs):
        if not has_orbat_permission(request.user, OrbatActions.MANAGE_UNIT_APPLICATIONS):
            raise PermissionDenied("You do not have permission to perform this action.")
        return super().dispatch(request, *args, **kwargs)


    def _redirect(self, app=None):
        """Redirect back to the same page (or base page if no app)."""
        if app:
            return redirect("orbat_applications_onboarding", pk=app.pk)
        return redirect(reverse("orbat_applications_onboarding_list"))

    def post(self, request, *args, **kwargs):
        app = self._get_application()
        if not app:
            return self._redirect()

        # Determine action
        method = request.POST.get('_method', 'create').lower()

        if method == 'delete':
            if not app.user:
                self.add_message("No user found to delete.", level=messages.ERROR)
                return self._redirect(app)
            user = app.user
            name = user.display_name
            user.delete()
            app.user = None
            app.save()
            self.add_message(f"User {name} deleted.", level=messages.INFO)
            return self._redirect(app)

        # For create / update
        name = request.POST.get('name', '').strip()
        teamspeak_id = request.POST.get('teamspeak_id') or None
        over_18 = request.POST.get('over18') == 'true'

        User = get_user_model()

        if method == 'create':
            if not name:
                self.add_message("Name is required to create a user.", level=messages.ERROR)
                return self._redirect(app)
            if User.objects.filter(display_name=name).exists():
                self.add_message(f"A user with the name '{name}' already exists.", level=messages.ERROR)
                return self._redirect(app)
            user = User.objects.create(
                username=name,
                display_name=name,
                status=UserStatus.APPLICANT,
                membership=None,
            )
            app.user = user
            app.teamspeak_id = teamspeak_id
            app.over_18 = over_18
            app.save()
            self.add_message(f"User '{user.display_name}' created.", level=messages.INFO)
            return self._redirect(app)

        elif method == 'update':
            if app.user:
                user = app.user
                if name:
                    user.display_name = name
                    user.username = name
                    user.save(update_fields=["display_name", "username"])
            app.teamspeak_id = teamspeak_id
            app.over_18 = over_18
            app.save()
            if app.user:
                self.add_message(f"Application for '{app.user.display_name}' updated.", level=messages.INFO)
            else:
                self.add_message(f"Application for {app.external_account.username} updated.", level=messages.INFO)
            return self._redirect(app)

        # Fallback
        return self._redirect(app)


class UnitApplicationApproveView(ORBATContextMixin, UnitHubTemplateView):
    def dispatch(self, request, *args, **kwargs):
        if not has_orbat_permission(request.user, OrbatActions.MANAGE_UNIT_APPLICATIONS):
            raise PermissionDenied("You do not have permission to perform this action.")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk, *args, **kwargs):
        app = get_object_or_404(UnitApplication, pk=pk, closed=False)

        if not app.user:
            messages.error(request, "Cannot approve an application without a user.")
            return redirect("orbat_applications_onboarding", pk=pk)

        try:
            app.approve(actioned_by=request.user)
        except ValidationError as e:
            messages.error(request, e.message)
            return redirect("orbat_applications_onboarding", pk=pk)

        profile_url = reverse(
            "user_profile",
            kwargs={"user_id": app.user.pk}
        )
        messages.success(
            request,
            format_html(
                "Application approved. User profile: <a href='{}'>{}</a>",
                profile_url,
                app.user.display_name,
            )
        )

        return redirect("orbat_applications_onboarding_list")

class UnitApplicationDenyView(ORBATContextMixin, UnitHubTemplateView):
    def dispatch(self, request, *args, **kwargs):
        if not has_orbat_permission(request.user, OrbatActions.DENY_UNIT_APPLICATIONS):
            raise PermissionDenied("You do not have permission to perform this action.")
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, pk, *args, **kwargs):
        app = get_object_or_404(UnitApplication, pk=pk, closed=False)

        reason = request.POST.get("reason", "").strip()

        try:
            app.deny(actioned_by=request.user, reason=reason)
        except ValidationError as e:
            messages.error(request, e.message)
            return redirect("orbat_applications_onboarding", pk=pk)

        if app.user:
            profile_url = reverse(
                "user_profile",
                kwargs={"user_id": app.user.pk}
            )
            messages.warning(
                request,
                format_html(
                    "Application denied. User profile: <a href='{}'>{}</a>",
                    profile_url,
                    app.user.display_name,
                )
            )
        else:
            messages.warning(
                request,
                f"Application denied for {app.external_account.username}."
            )

        return redirect("orbat_applications_onboarding_list")
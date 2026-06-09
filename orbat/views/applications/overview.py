from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.validators import RegexValidator
from django.shortcuts import redirect

from common.views import UnitHubTemplateView
from external_auth.models import DiscordAccount
from orbat.enums import OrbatActions
from orbat.models.sections import SectionApplication
from orbat.models.unit import UnitApplication
from orbat.selectors import get_section_slot
from orbat.views.mixins import ORBATContextMixin
from permissions.engine import has_orbat_permission

ACTION_MAP = {
    "create_unit_application": {
        "perm": OrbatActions.CREATE_UNIT_APPLICATIONS,
        "handler": "_create_unit_application",
    }
}

class ORBATApplicationOverview(ORBATContextMixin, UnitHubTemplateView):
    template_name = 'orbat/applications/overview.html'

    breadcrumbs = [
        ("Applications", None)
    ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["unit_application_can_manage"] = has_orbat_permission(
            self.request.user,
            OrbatActions.MANAGE_UNIT_APPLICATIONS,
        )

        context["unit_application_can_create"] = has_orbat_permission(
            self.request.user,
            OrbatActions.CREATE_UNIT_APPLICATIONS,
        )

        context["unit_application_perms"] = (
                context["unit_application_can_manage"]
                or context["unit_application_can_create"]
        )

        if context["unit_application_perms"]:
            context["unit_applications"] = (
                UnitApplication.objects
                .filter(processed_date=None)
                .order_by("date")
            )

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

    def post(self, request, *args, **kwargs):
        action = request.POST.get("action")
        config = ACTION_MAP.get(action)

        if not config:
            raise PermissionDenied()

        if not has_orbat_permission(request.user, config["perm"]):
            raise PermissionDenied()

        # Execute handler
        handler = getattr(self, config["handler"])
        response = handler(request)

        return response or redirect(self.request.path)

    def _create_unit_application(self, request, *args, **kwargs):
        discord_id = request.POST.get("discord_id", "").strip()
        discord_username = request.POST.get("discord_username", "").strip()

        if not DiscordAccount.is_valid_discord_id(discord_id):
            self.add_message("Invalid Discord ID", messages.WARNING)
            return None

        discord_account, created = DiscordAccount.objects.get_or_create(
            external_id=discord_id,
            defaults={"username": discord_username}
        )

        if not created and discord_account.username != discord_username:
            discord_account.username = discord_username
            discord_account.save(update_fields=["username"])

        if discord_account.user and discord_account.user.is_active:
            self.add_message("This account is already active", messages.WARNING)
            return None

        if not discord_account.can_create_application:
            self.add_message("There was a conflict with this application", messages.WARNING)
            return None

        application = UnitApplication.objects.create(
            external_account=discord_account,
            status=UnitApplication.STATUS_WAITING_REPLY
        )

        self.add_message("Created new unit application", messages.SUCCESS)
        return redirect("orbat_applications_onboarding", pk=application.pk)
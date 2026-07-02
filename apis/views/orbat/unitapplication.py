from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from apis.views.base import OrbatAPIView
from external_auth.models import DiscordAccount
from orbat.enums import OrbatActions
from orbat.models.unit import UnitApplication

from django.contrib.auth import get_user_model


User = get_user_model()

def generate_unique_username(base_username):
    username = base_username
    counter = 1

    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1

    return username

class UnitApplicationAPI(OrbatAPIView):
    """
    GET -> Get a list of current applications
    POST -> Create a new unit application (Discord only)
    """
    object_permission_required = False
    required_permissions = {
        "GET": [OrbatActions.VIEW_UNIT_APPLICATIONS],
        "POST": [OrbatActions.CREATE_UNIT_APPLICATIONS]
    }

    def get(self, request, *args, **kwargs):
        applications = UnitApplication.objects.filter(closed=False)

        applications_data = []
        for application in applications:
            applications_data.append({
                "id": application.pk,
                "status": application.status,
                "creation_date": application.date,
                "discord_id": application.external_account.external_id,
                "discord_name": application.external_account.username,
            })

        return Response(applications_data)

    def post(self, request, *args, **kwargs):
        data = request.data

        discord_id = (data.get("discord_id") or "").strip()
        username = (data.get("username") or "").strip()
        profile_url = data.get("profile_url")

        if not discord_id:
            return Response({"error": "discord_id is required."}, status=400)

        if not username:
            return Response({"error": "username is required."}, status=400)

        discord_account, _ = DiscordAccount.objects.get_or_create(
            external_id=discord_id,
            defaults={
                "username": username,
                "profile_url": profile_url,
            }
        )

        if discord_account.user and discord_account.user.is_active:
            return Response({"error": "active user already exists"}, status=409)

        if not discord_account.can_create_application:
            return Response({"error": "conflict on application"}, status=400)

        user = discord_account.user

        if not user:
            unique_username = generate_unique_username(username)

            user = User.objects.create(
                username=unique_username,
            )

            discord_account.user = user
            discord_account.save(update_fields=["user"])

        application = UnitApplication.objects.create(
            user=user,
            external_account=discord_account,
            status=UnitApplication.STATUS_WAITING_REPLY,
        )

        return Response(
            {
                "success": True,
                "id": application.pk,
                "status": application.status,
            },
            status=status.HTTP_201_CREATED,
        )

class UnitApplicationQuestionnaireAPI(OrbatAPIView):
    """
    PATCH   -> Update the details of a questionnaire
    """

    required_permissions = {
        "PATCH": [OrbatActions.MANAGE_UNIT_APPLICATIONS],
    }

    def get_object(self):
        return get_object_or_404(UnitApplication, pk=self.kwargs["pk"])

    def patch(self, request, *args, **kwargs):
        application = self._object
        data = request.data

        questionnaire = application.questionnaire

        fields = {
            "preferred_display_name": str,
            "owns_arma3": bool,
            "birth_year": int,
            "timezone": str,
            "has_used_tfar": bool,
            "has_used_ace": bool,
            "seriousness_ranking": int,
            "referral_source": str,
            "previous_groups": str,
        }

        for field, expected_type in fields.items():
            if field not in data:
                continue
            value = data[field]

            if not isinstance(value, expected_type):
                return Response({"error": f"{field} must be a {expected_type.__name__}"}, status=400)
            setattr(questionnaire, field, value)

        questionnaire.full_clean()
        questionnaire.save()

        return Response({"success": True, "id": application.pk})
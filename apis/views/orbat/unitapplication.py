from rest_framework import status
from rest_framework.response import Response

from apis.views.base import OrbatAPIView
from external_auth.models import DiscordAccount
from orbat.enums import OrbatActions
from orbat.models.unit import UnitApplication


class UnitApplicationAPI(OrbatAPIView):
    """
    POST -> Create a new unit application (Discord only)
    """
    object_permission_required = False
    required_permissions = {
        "POST": [OrbatActions.CREATE_UNIT_APPLICATIONS]
    }

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
            return Response({"error": "active user already exists"}, status=400)

        if not discord_account.can_create_application:
            return Response({"error": "conflict on application"}, status=400)

        application = UnitApplication.objects.create(
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
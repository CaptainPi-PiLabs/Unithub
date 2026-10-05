from rest_framework import status
from rest_framework.response import Response

from apis.views.base import ArmaAPIView
from external_auth.models import SteamAccount
from permissions.permission_modules.ArmaActions import ArmaActions


class ArmaCheckPlayerAPI(ArmaAPIView):
    """
    POST -> Check whether a Steam player is known to UnitHub.
    """
    object_permission_required = False
    required_permissions = {
        "POST": [ArmaActions.CHECK_PLAYER]
    }

    def post(self, request, *args, **kwargs):
        steam_id = request.data.get("steam_id")
        username = request.data.get("username")

        if not steam_id:
            return Response(
                {"detail": "steam_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not username:
            return Response(
                {"detail": "username is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        steam_account = SteamAccount.objects.filter(
            external_id=steam_id
        ).first()

        if steam_account:
            return Response({
                "known": True,
            })

        steam_account, created = SteamAccount.objects.get_or_create(
            external_id=steam_id,
            defaults={
                "username": username,
            },
        )

        if not created and steam_account.username != username:
            steam_account.username = username
            steam_account.save(update_fields=["username"])

        return Response({
            "known": False,
        })
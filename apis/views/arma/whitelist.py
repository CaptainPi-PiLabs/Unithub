
from django.db.models import OuterRef, Q
from django.utils import timezone
from rest_framework.response import Response

from apis.views.base import ArmaAPIView
from external_auth.models import SteamAccount
from permissions.permission_modules.ArmaActions import ArmaActions


class ArmaGetWhitelistAPI(ArmaAPIView):
    """
    GET -> Get the current Arma whitelist.
    """

    object_permission_required = False
    required_permissions = {
        "GET": [ArmaActions.READ_WHITELIST]
    }

    def get(self, request, *args, **kwargs):
        today = timezone.now().date()

        accounts = (
            SteamAccount.objects.filter(
                user__isnull=False,
                user__unit_memberships__start_date__lte=today,
            )
            .filter(
                Q(user__unit_memberships__end_date__isnull=True)
                | Q(user__unit_memberships__end_date__gte=today)
            )
            .values("external_id", "username")
            .distinct()
        )

        whitelist = [
            {
                "steam_id": account["external_id"],
                "username": account["username"],
            }
            for account in accounts
        ]

        return Response(whitelist)
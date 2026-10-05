from django.db.models import OuterRef, Q
from django.utils import timezone
from rest_framework.response import Response

from apis.views.base import ArmaAPIView
from external_auth.models import SteamAccount
from permissions.permission_modules.ArmaActions import ArmaActions
from users.models import UnitMembership


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

        steam_ids = list(
            SteamAccount.objects.filter(
                user__isnull=False,
                user__unit_memberships__start_date__lte=today,
            ).filter(
                Q(user__unit_memberships__end_date__isnull=True) |
                Q(user__unit_memberships__end_date__gte=today)
            ).values_list(
                "external_id",
                flat=True,
            ).distinct()
        )

        return Response(steam_ids)
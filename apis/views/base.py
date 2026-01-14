from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

from apis.models import UserAPIKey, ServiceAPIKey
from permissions.models import PermissionRule
from permissions.engine import has_permission


class BaseAPIView(APIView):
    renderer_classes = [JSONRenderer]
    module = None
    required_permissions = {
        "GET": [],
    }

    def _get_api_key(self):
        api_key_value = self.request.headers.get('X-API-KEY')
        if not api_key_value:
            return None

        for KeyModel in [UserAPIKey, ServiceAPIKey]:
            key = KeyModel.objects.filter(key=api_key_value).first()
            if key:
                return key

        return None

    def _check_permissions(self, subject, method, scope=None):
        if not self.module:
            return False
        perms = self.required_permissions.get(method)
        if perms is None:
            raise PermissionDenied("Insufficient permissions")

        for action in perms:
            rule = PermissionRule.objects.get(
                module=self.module,
                action=action.value,
            )

            if not has_permission(subject, rule, scope=scope):
                return False
        return True

    def context_check(self, request, method, user, *args, **kwargs):
        if method == "GET":
            return True
        return False

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)

        method = request.method.upper()
        key = self._get_api_key()

        user = request.user if request.user.is_authenticated else None
        if not user and key and getattr(key, "user", None):
            user = key.user

        # Require authentication if neither key nor user
        if not key and not user:
            raise NotAuthenticated()

        subject = key or user

        if isinstance(key, ServiceAPIKey) and key.allowed_ips:
            client_ip = request.META.get("REMOTE_ADDR")
            if not key.is_ip_allowed(client_ip):
                raise PermissionDenied("IP not allowed")

        if not self._check_permissions(subject, method):
            raise PermissionDenied("Insufficient permissions")

        # Attach key info to request for use in view
        request.api_key = key
from rest_framework import status
from rest_framework.renderers import JSONRenderer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotAuthenticated, PermissionDenied

from apis.models import UserAPIKey, ServiceAPIKey


class BaseAPIView(APIView):
    renderer_classes = [JSONRenderer]
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

    def _check_permissions_for_key(self, key, perms):
        if not perms:
            return True

        for perm in perms:
            if hasattr(key, "has_permission"):
                if not key.has_permission(perm):
                    return False
            else:  # fallback to Django user
                if not key.has_perm(perm):
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

        if key:
            if key.get_type() == "service" and key.allowed_ips:
                client_ip = request.META.get("REMOTE_ADDR")
                if not key.is_ip(client_ip):
                    raise PermissionDenied("Insufficient permissions")

            perms = self.required_permissions.get(method)
            if method == "GET" and perms is None:
                perms = []
            elif perms is None:
                raise PermissionDenied("Insufficient permissions")

            if not self._check_permissions_for_key(key, perms):
                raise PermissionDenied("Insufficient permissions")

        if user:
            if not self.context_check(request, method, user, *args, **kwargs):
                print("User is missing context permissions")
                raise PermissionDenied("Insufficient permissions")

        # Attach key info to request for use in view
        request.api_key = key
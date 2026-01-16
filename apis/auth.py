from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from apis.models import APIKeyBase, UserAPIKey, ServiceAPIKey


class APIKeyAuthentication(BaseAuthentication):
    def get_client_ip(self, request):
        ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR"))
        if ip and "," in ip:
            ip = ip.split(",")[0].strip()
        return ip

    def authenticate(self, request):
        api_key_value  = request.headers.get("X-API-KEY")
        if not api_key_value :
            return None  # no key provided → let DRF handle anonymous

        hashed_key = APIKeyBase.hash_key(api_key_value)

        for KeyModel in (UserAPIKey, ServiceAPIKey):
            try:
                key = KeyModel.objects.get(key=hashed_key)
                if not getattr(key, "active", False):
                    raise AuthenticationFailed("API key expired or disabled")

                client_ip = self.get_client_ip(request)
                if isinstance(key, ServiceAPIKey) and key.allowed_ips:
                    if not key.is_ip_allowed(client_ip):
                        raise AuthenticationFailed("IP not allowed")

                key.last_used_at = timezone.now()
                key.last_used_ip = client_ip
                key.save(update_fields=["last_used_at", "last_used_ip"])

                user = getattr(key, "user", None)
                return user, key

            except KeyModel.DoesNotExist:
                continue

        raise AuthenticationFailed("Invalid API key")

    def authenticate_header(self, request):
        return "Api-Key"
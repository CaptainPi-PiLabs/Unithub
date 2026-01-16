from django.db import models

from core import settings


class APIKeyBase(models.Model):
    key = models.CharField(max_length=64, unique=True, editable=False)
    name = models.CharField(max_length=64, help_text="Label for the key")
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)
    last_used_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        abstract = True

    @staticmethod
    def hash_key(raw_key):
        import hashlib
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

    @staticmethod
    def generate_key():
        import secrets
        return secrets.token_hex(32)

    def has_permission(self, module, action, scope=None):
        from permissions.engine import has_permission
        return has_permission(self, module, action, scope)

    def save(self, *args, **kwargs):
        if not self.key:
            raw_key = self.generate_key()
            self.key = self.hash_key(raw_key)
            self._raw_key = raw_key # Store if needed to return one time in a view
        super().save(*args, **kwargs)


class UserAPIKey(APIKeyBase):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="api_key")

    def is_ip_allowed(self, ip):
        return True

    def get_type(self):
        return "user"

class ServiceAPIKey(APIKeyBase):
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="created_service_api_keys")
    allowed_ips = models.TextField(blank=True, help_text="Comma-separated List of allowed IP addresses. Leave empty for no restrictions.")

    def is_ip_allowed(self, ip):
        if not self.allowed_ips:
            return True
        allowed = [ip.strip() for ip in self.allowed_ips.split(",")]
        return ip in allowed

    def get_type(self):
        return "service"
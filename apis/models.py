from django.db import models

from core import settings


class Permissions(models.TextChoices):
    ADD_USER = "add_user", "Add User"
    ADD_SECTION = "add_section", "Add Section"
    ASSIGN_SECTION = "assign_section", "Assign Section"

class APIKeyBase(models.Model):
    key = models.CharField(max_length=64, unique=True, editable=False)
    name = models.CharField(max_length=64, help_text="Label for the key")
    create_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def generate_key(self):
        import secrets
        return secrets.token_hex(32)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        super().save(*args, **kwargs)

class UserAPIKey(APIKeyBase):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="api_key")

    def is_ip_allowed(self, ip):
        return True

    def has_permission(self, permission):
        if self.user.is_staff:
            return True
        return False

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

    def has_permission(self, permission: str):
        if isinstance(permission, Permissions):
            permission = permission.value
        return self.permissions.filter(name=permission).exists()

    def get_type(self):
        return "service"

class KeyPermission(models.Model):
    key = models.ForeignKey(ServiceAPIKey, on_delete=models.CASCADE, related_name="permissions")
    name = models.CharField(max_length=50, choices=Permissions.choices)

    class Meta:
        unique_together = ("key", "name")

    def __str__(self):
        return f"{self.key.name} -> {self.name}"
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q


class PermissionGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class PermissionGroupMembership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    group = models.ForeignKey(PermissionGroup, on_delete=models.CASCADE, related_name="memberships")

    def __str__(self):
        return f"{self.user.display_name}"

class PermissionModule(models.TextChoices):
    ORBAT = "orbat", "ORBAT"
    EVENTS = "events", "EVENTS"
    TRAINING = "training", "TRAINING"
    INTEGRATIONS = "integrations", "INTEGRATIONS"

class PermissionRule(models.Model):
    module = models.CharField(max_length=32, choices=PermissionModule.choices)
    action = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.module} - {self.action}"

class PermissionGrant(models.Model):
    ALLOW = 'allow'
    DENY = 'deny'

    rule = models.ForeignKey(PermissionRule, on_delete=models.CASCADE, related_name="grants")
    effect = models.CharField(max_length=5, choices=[(ALLOW, "Allow"), (DENY, "Deny")], default=ALLOW)

    # ---- SUBJECT (exactly one must be set) ----
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.CASCADE
    )
    group = models.ForeignKey(
        PermissionGroup,
        null=True, blank=True,
        on_delete=models.CASCADE,
        related_name="grants",
    )
    service_api_key = models.ForeignKey(
        "apis.ServiceAPIKey",
        null=True, blank=True,
        on_delete=models.CASCADE
    )
    user_api_key = models.ForeignKey(
        "apis.UserAPIKey",
        null=True, blank=True,
        on_delete=models.CASCADE
    )

    # ---- SCOPE ----
    content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.CASCADE)
    # content_object = GenericForeignKey("content_type", "object_id")
    object_id = models.PositiveIntegerField(null=True, blank=True)
    scope_key = models.CharField(max_length=20, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Permission Grant"
        verbose_name_plural = "Permission Grants"

        constraints = [
            models.CheckConstraint(
                name="exactly_one_subject",
                condition=
                    Q(user__isnull=False, group__isnull=True, service_api_key__isnull=True, user_api_key__isnull=True) |
                    Q(user__isnull=True, group__isnull=False, service_api_key__isnull=True, user_api_key__isnull=True) |
                    Q(user__isnull=True, group__isnull=True, service_api_key__isnull=False, user_api_key__isnull=True) |
                    Q(user__isnull=True, group__isnull=True, service_api_key__isnull=True, user_api_key__isnull=False)
            )
        ]
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models

from permissions.contrants import PERMISSIONS


# Create your models here.
class PermissionGroup(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class PermissionGroupMembership(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    group = models.ForeignKey(PermissionGroup, on_delete=models.CASCADE, related_name="memberships")

    def __str__(self):
        return f"{self.user.display_name}"

class PermissionGrant(models.Model):
    ALLOW = 'allow'
    DENY = 'deny'
    EFFECT_CHOICES = [(ALLOW, 'Allow'), (DENY, 'Deny'), ]

    MODULE_CHOICES = [(m, m.title()) for m in PERMISSIONS]

    group = models.ForeignKey(PermissionGroup, on_delete=models.CASCADE, related_name="grants")
    permission = models.CharField(max_length=100)
    module = models.CharField(max_length=50,choices=MODULE_CHOICES,help_text="Module this permission applies to")
    effect = models.CharField(max_length=5, choices=EFFECT_CHOICES, default=ALLOW)

    content_type = models.ForeignKey(ContentType, null=True, blank=True, on_delete=models.CASCADE)
    content_object = GenericForeignKey("content_type", "object_id")
    object_id = models.PositiveIntegerField(null=True, blank=True)
    scope_key = models.CharField(max_length=20, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Permission Grant"
        verbose_name_plural = "Permission Grants"
        unique_together = ("module", "permission", "content_type", "object_id", "effect")

    def target_name(self):
        """Return a human-readable target for this grant."""
        if self.object_id and self.content_object:
            # Use the name of the object instead of ID
            return str(self.content_object)
        # Wildcard if no object
        return "*"

    def __str__(self):
        return f"{self.module}.{self.target_name()}.{self.permission}: {self.effect.upper()}"

    def get_scope_name(self):
        """Human-readable scope name."""
        if self.content_object is None:
            return "Global"
        if hasattr(self.content_object, "get_permission_name"):
            return self.content_object.get_permission_name()
        return str(self.content_object)

    def get_permission_choices(self):
        """
        Return the available actions for the selected module.
        Used in forms/admin to dynamically show valid actions.
        """
        return [(p, p.replace("_", " ").title()) for p in PERMISSIONS.get(self.module, [])]
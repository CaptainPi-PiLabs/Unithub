from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from common.admin_logging import log_admin_addition
from common.temporal.models import ApplicationBase
from users.models import UnitMembership


class UnitApplication(ApplicationBase):
    STATUS_WAITING_REPLY = "waiting_reply"
    STATUS_BCT_PLANNED = "bct_planned"
    STATUS_PASSED = "passed"

    STATUS_CHOICES = ApplicationBase.STATUS_CHOICES + [
        (STATUS_WAITING_REPLY, "Waiting reply"),
        (STATUS_BCT_PLANNED, "BCT planned"),
        (STATUS_PASSED, "Passed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    external_account = models.ForeignKey(
        "external_auth.DiscordAccount",
        on_delete=models.CASCADE
    )
    teamspeak_id = models.PositiveIntegerField(null=True, blank=True)
    over_18 = models.BooleanField(default=False)

    def __str__(self):
        return self.external_account.username

    def clean(self):
        super().clean()

        if not self.closed:
            qs = UnitApplication.objects.filter(
                external_account=self.external_account,
                closed=False
            ).exclude(pk=self.pk)
            if qs.exists():
                raise ValidationError("This Discord account already has an open application.")

        if self.external_account.user and self.external_account.user.is_active and not self.closed:
            raise ValidationError("Cannot create an application: Discord account already linked to an active user.")

    def approve(self, actioned_by=None):
        if not self.user:
            raise ValidationError("Cannot approve application without a user.")
        from users.models import UserStatus

        # Promote user
        self.user.status = UserStatus.ACTIVE
        self.user.save()
        membership = UnitMembership.objects.create(user=self.user)

        if actioned_by:
            log_admin_addition(actioned_by, membership, "Created during application approval")

        # Close application
        self.status = self.STATUS_PASSED
        self.closed = True
        self.actioned_by = actioned_by or self.actioned_by
        self.processed_date = timezone.now()
        self.save(update_fields=[
            "status",
            "closed",
            "actioned_by",
            "processed_date",
        ])

    def deny(self, actioned_by=None, reason=None):
        self.status = self.STATUS_DENIED
        self.closed = True
        self.actioned_by = actioned_by or self.actioned_by
        self.comment = reason or ""
        self.processed_date = timezone.now()
        self.save(update_fields=[
            "status",
            "closed",
            "actioned_by",
            "processed_date",
            "comment",
        ])
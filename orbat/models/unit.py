from zoneinfo import available_timezones

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from timezone_field import TimeZoneField

from common.admin_logging import log_admin_addition
from common.temporal.models import ApplicationBase
from integrations.events import EventType
from integrations.services import publish
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

    def get_absolute_url(self):
        return reverse(
            "orbat_applications_onboarding",
            kwargs={"pk": self.pk},
        )

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

        if not self.questionnaire or not self.questionnaire.is_complete():
            raise ValidationError("Questionnaire is incomplete.")
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
        publish(
            EventType.MEMBER_APPROVED,
            application_id=self.pk,
            user_id=self.user.pk,
            discord_id=self.external_account.external_id,
        )

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
        publish(
            EventType.MEMBER_REJECTED,
            application_id=self.pk,
            user_id=self.user.pk,
            discord_id=self.external_account.external_id,
        )

class AreasOfInterest(models.Model):
    name = models.CharField(max_length=50)
    display = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


def validate_timezone(value):
    if value not in available_timezones():
        raise ValidationError("Invalid timezone")


class UnitApplicationQuestionnaire(models.Model):
    application = models.OneToOneField(
        UnitApplication,
        on_delete=models.CASCADE,
        related_name="questionnaire",
    )

    preferred_display_name = models.CharField(max_length=50, blank=True)

    owns_arma3 = models.BooleanField(null=True, blank=True)
    birth_year = models.PositiveSmallIntegerField(null=True, blank=True)
    timezone = TimeZoneField(blank=True)

    has_used_tfar = models.BooleanField(null=True, blank=True)
    has_used_ace = models.BooleanField(null=True, blank=True)

    seriousness_ranking = models.PositiveSmallIntegerField(
        validators=[
            MinValueValidator(1),
            MaxValueValidator(10),
        ],
        null=True,
        blank=True,
    )

    areas_of_interest = models.ManyToManyField(AreasOfInterest, blank=True,)
    referral_source = models.CharField(max_length=255, blank=True)
    previous_groups = models.TextField(blank=True)

    def is_complete(self):
        return all([
            self.preferred_display_name.strip(),
            self.owns_arma3 is not None,
            self.birth_year,
            self.timezone,
            self.has_used_tfar is not None,
            self.has_used_ace is not None,
            self.seriousness_ranking,
        ])
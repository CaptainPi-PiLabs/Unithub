import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from orbat.models.unit import UnitApplication


class ExternalAccount(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_account",
    )
    external_id = models.CharField(max_length=64, unique=True)
    username = models.CharField(max_length=64)
    profile_url = models.URLField(blank=True, null=True)

    class Meta:
        abstract = True

class DiscordAccount(ExternalAccount):
    provider = models.CharField(max_length=20, default="discord", editable=False)

    def __str__(self):
        return f"Discord - {self.username}"

    @staticmethod
    def is_valid_discord_id(value: str) -> bool:
        if not value:
            return False
        return bool(re.fullmatch(r"\d{17,19}", value))

    @classmethod
    def validate_discord_id(cls, value: str):
        if not cls.is_valid_discord_id(value):
            raise ValidationError(f"Discord ID must be 17-19 digits")

    def clean(self):
        super().clean()
        DiscordAccount.validate_discord_id(self.external_id)

    @property
    def can_create_application(self):
        """
        Returns True if this Discord account is allowed to create a new UnitApplication.
        Rules:
        1. No open application exists for this account.
        2. Either no user exists or the linked user is inactive.
        """
        if self.user and self.user.is_active:
            return False

        open_apps_exist = UnitApplication.objects.filter(
            external_account=self, closed=False
        ).exists()

        return not open_apps_exist

class SteamAccount(ExternalAccount):
    provider = models.CharField(max_length=20, default="steam")

    def __str__(self):
        return f"Steam - {self.username}"

class TeamSpeakAccount(ExternalAccount):
    provider = models.CharField(max_length=20, default="teamspeak")
    def __str__(self):
        return f"TeamSpeak - {self.username}"
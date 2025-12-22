from django.db import models

from unithub import settings


# Create your models here.
class ExternalAccount(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="%(class)s_account",
    )
    external_id = models.CharField(max_length=64, unique=True)
    username = models.CharField(max_length=64)
    profile_url = models.URLField(blank=True, null=True)

    class Meta:
        abstract = True

class DiscordAccount(ExternalAccount):
    provider = models.CharField(max_length=20, default="discord")

    def __str__(self):
        return f"Discord - {self.username}"

class SteamAccount(ExternalAccount):
    provider = models.CharField(max_length=20, default="steam")

    def __str__(self):
        return f"Steam - {self.username}"

class TeamSpeakAccount(ExternalAccount):
    provider = models.CharField(max_length=20, default="teamspeak")
    def __str__(self):
        return f"TeamSpeak - {self.username}"
from django.conf import settings
from django.db import models

from events.models import Event


class Attendance(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="attendances")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    first_join = models.DateTimeField(null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    # Could also add a flag if they left early or disconnected
    manual = models.BooleanField(default=False)
    left_early = models.BooleanField(default=False)

    class Meta:
        unique_together = ("event", "user")
        ordering = ["event", "first_join"]

    def __str__(self):
        return f"{self.user.display_name} - {self.event.name} ({'Manual' if self.manual else 'Auto'})"
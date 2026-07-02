from datetime import timedelta

from django.db import models
from django.utils import timezone

from .events import EventType

STALE_AFTER = timedelta(minutes=30)

class IntegrationEvent(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        PUBLISHED = "published", "Published"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        ERRORED = "errored", "Errored"
        FAILED = "failed", "Failed"
        CANCELLED = "cancelled", "Cancelled"

    event_type = models.CharField(max_length=50, choices=EventType.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    payload = models.JSONField()
    attempts = models.PositiveIntegerField(default=0)
    processing_started = models.DateTimeField(null=True, blank=True)
    error = models.TextField(blank=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @property
    def is_claimable(self):
        if self.status in {
            self.Status.PENDING,
            self.Status.PUBLISHED,
            self.Status.ERRORED,
        }:
            return True

        if self.status == self.Status.PROCESSING:
            if self.processing_started is None:
                return True
            if self.attempts > 3:
                return False
            return self.processing_started < timezone.now() - STALE_AFTER

        return False
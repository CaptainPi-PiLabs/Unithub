from django.contrib.contenttypes.fields import GenericForeignKey
from django.db import models
from django.utils import timezone

from unithub import settings


class TimelineTypes(models.TextChoices):
    UNIT_JOINED = "UNIT_JOINED", "joined the unit"
    UNIT_LEFT = "UNIT_LEFT", "left the unit"
    SECTION_JOINED = "SECTION_JOINED", "joined the section"
    SECTION_LEFT = "SECTION_LEFT", "left the section"
    ROLE_ASSIGNED = "ROLE_ASSIGNED", "assigned to a role"
    AWARD_RECEIVED = "AWARD_RECEIVED", "received an award"
    TRAINING_COMPLETED = "TRAINING_COMPLETED", "training completed"


class TimelineEntry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    section = models.ForeignKey('orbat.Section', null=True, blank=True, on_delete=models.SET_NULL)
    timestamp = models.DateTimeField(default=timezone.now)
    event_type = models.CharField(max_length=50, choices=TimelineTypes.choices)
    snapshot_name = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(blank=True)
    content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    related_object = GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.user.display_name} {self.get_event_type_display()}'

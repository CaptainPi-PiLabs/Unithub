from django.db import models

from orbat.models import Section
from core.mixins.model_mixin import OrderedModelMixin


class Campaign(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.name

class Event(models.Model):
    EVENT_TYPE_CHOICES = [
        ('OP', 'Operation'),
        ('SI', 'Side OP'),
        ('TR', 'Training'),
        ('CO', 'Community'),
        ('OT', 'Other'),
    ]

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    date = models.DateField()
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True, blank=True, related_name='events')
    start_time = models.TimeField()
    end_time = models.TimeField()
    type = models.CharField(max_length=2, choices=EVENT_TYPE_CHOICES)

    class Meta:
        ordering = ["-date", "start_time"]

    def __str__(self):
        return f"{self.name}"

    @property
    def organizers(self):
        return self.roles.filter(role='Organizer')

class EventGroup(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="groups")
    orbat_section = models.ForeignKey(Section, on_delete=models.SET_NULL, null=True, related_name="event_sections")
    name = models.CharField(max_length=50)  # "Alpha", "Bravo", etc.

    class Meta:
        unique_together = ("event", "name")

class EventAssignment(OrderedModelMixin, models.Model):
    STATUS = [
        ('YES', 'Attending'),
        ('NO', 'Not Attending'),
        ('LATE', 'Late'),
        ('MAYBE', 'Maybe'),
    ]
    COLOUR_CHOICES = [
        ("Gold", "Gold"),
        ("Green", "Green"),
        ("Red", "Red"),
        ("Blue", "Blue"),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="assignments")
    user = models.ForeignKey("users.CustomUser", on_delete=models.CASCADE)
    status = models.CharField(max_length=5, choices=STATUS, default='YES')
    event_group = models.ForeignKey(EventGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name="assignments")
    role = models.CharField(max_length=50, blank=True)
    colour = models.CharField(max_length=5, null=True, blank=True, choices=COLOUR_CHOICES)
    assigned_by = models.ForeignKey(
        "users.CustomUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_players"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    assigned_at = models.DateTimeField(null=True, blank=True)

    # class Meta:
        # unique_together = ("event_group", "user")
        # ordering = ['group', 'order']

class EventRole(models.Model):
    ROLE_CHOICES = [
        ('ORGANIZER', 'Organizer'),
        ('ASSIST', 'Assistant'),
        ('CO', 'Commanding Officer'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="roles")
    user = models.ForeignKey("users.CustomUser", on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)

    class Meta:
        unique_together = ("event", "user", "role")
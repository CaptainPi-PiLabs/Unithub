from django.conf import settings
from django.db import models

from events.models import Event


class Qualification(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

class QualificationCriterion(models.Model):
    qualification = models.ForeignKey(
        "Qualification",
        on_delete=models.CASCADE,
        related_name="criteria"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)  # custom order

    class Meta:
        ordering = ["order"]
        unique_together = ("qualification", "order")

    def __str__(self):
        return f"{self.qualification.name} - {self.description}"


class QualificationEvent(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name="qualification_events")
    qualification = models.ForeignKey("training.Qualification", on_delete=models.CASCADE, related_name="qualification_events")

    class Meta:
        unique_together = ("event", "qualification")

    def __str__(self):
        return f"{self.qualification.name} @ {self.event.name}"

class UserQualification(models.Model):
    """
    Tracks which users have earned which qualifications
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    qualification = models.ForeignKey(Qualification, on_delete=models.CASCADE)
    date_awarded = models.DateField(null=True, blank=True)
    latest_passed = models.DateField(null=True, blank=True)
    awarded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="qualifications_awarded")

    class Meta:
        unique_together = ("user", "qualification")

    def __str__(self):
        return f"{self.user.display_name} - {self.qualification.name}"

class UserQualificationCriterion(models.Model):
    """
    Tracks which criteria a user has completed for a qualification.
    The existence of the entry implies the criterion was satisfied.
    """
    user_qualification = models.ForeignKey(
        "UserQualification",
        on_delete=models.CASCADE,
        related_name="criteria_status"
    )
    criterion = models.ForeignKey(QualificationCriterion, on_delete=models.CASCADE)
    completed_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user_qualification", "criterion")
        ordering = ["criterion__order"]

    def __str__(self):
        return f"{self.user_qualification.user.display_name} - {self.criterion.description}"

class QualificationTrainer(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    qualification = models.ForeignKey(Qualification, on_delete=models.CASCADE)
    is_manager = models.BooleanField(default=False)
    is_senior = models.BooleanField(default=False)
    is_trainer = models.BooleanField(default=True)
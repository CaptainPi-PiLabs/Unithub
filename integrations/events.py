from django.db import models


class EventType(models.TextChoices):
    MEMBER_APPROVED = "member_approved"
    MEMBER_REJECTED = "member_rejected"
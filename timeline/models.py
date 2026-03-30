from django.db import models


class TimelineTypes(models.TextChoices):
    UNIT_JOINED = "UNIT_JOINED", "joined the unit"
    UNIT_LEFT = "UNIT_LEFT", "left the unit"
    SECTION_JOINED = "SECTION_JOINED", "joined the section"
    SECTION_LEFT = "SECTION_LEFT", "left the section"
    ROLE_ASSIGNED = "ROLE_ASSIGNED", "assigned to a role"
    AWARD_RECEIVED = "AWARD_RECEIVED", "received an award"
    TRAINING_COMPLETED = "TRAINING_COMPLETED", "training completed"
    MOVED_TO_LOA = "MOVED_TO_LOA", "moved to leave of absence"
    RETURNED_FROM_LOA = "RETURNED_FROM_LOA", "returned from leave of absence"
    MOVED_TO_RESERVES = "MOVED_TO_RESERVES", "moved to reserves"
    RETURNED_FROM_RESERVES = "RETURNED_FROM_RESERVES", "returned from reserves"
    MEMBERSHIP_TIER_CHANGED = "MEMBERSHIP_TIER_CHANGED", "membership updated"
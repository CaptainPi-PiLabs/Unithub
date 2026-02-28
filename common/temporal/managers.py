import datetime
from dataclasses import dataclass
from typing import Optional

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q


@dataclass
class TemporalChange:
    obj: models.Model
    action: str  # "delete", "trim_left", "trim_right"
    old_start: Optional[datetime.date]
    old_end: Optional[datetime.date]
    new_start: Optional[datetime.date]
    new_end: Optional[datetime.date]

class TemporalQuerySet(models.QuerySet):

    def overlaps(self, instance):
        qs = self
        qs = qs.exclude(pk=instance.pk)
        qs = qs.filter(
            Q(start_date__lte=instance.end_date or datetime.date.max) &
            Q(
                Q(end_date__isnull=True) |
                Q(end_date__gte=instance.start_date)
            )
        )

        for field in getattr(instance, "non_overlapping_fields", []):
            qs = qs.filter(**{field: getattr(instance, field)})

        return qs

    def analyze_clashes(self, instance):
        """
            Returns a list describing what WOULD change if this entry were applied.
            Does not modify the database.
            """
        changes = []
        overlaps = self.overlaps(instance).order_by("start_date")

        instance_start = instance.start_date
        instance_end = instance.end_date or datetime.date.max

        for overlap in overlaps:
            overlap_start = overlap.start_date
            overlap_end = overlap.end_date or datetime.date.max

            # Fully enclosed → delete
            if instance_start <= overlap_start and instance_end >= overlap_end:
                changes.append(TemporalChange(
                    obj=overlap,
                    action="delete",
                    old_start=overlap.start_date,
                    old_end=overlap.end_date,
                    new_start=None,
                    new_end=None,
                ))
                continue

            # Trim right: overlap starts before new range
            if overlap_start < instance_start and overlap_end >= instance_start:
                changes.append(TemporalChange(
                    obj=overlap,
                    action="trim_right",
                    old_start=overlap.start_date,
                    old_end=overlap.end_date,
                    new_start=overlap.start_date,
                    new_end=instance.start_date - datetime.timedelta(days=1),
                ))
                continue

            # Trim left: overlap ends after new range
            if instance_start < overlap_end and instance_end >= overlap_start:
                changes.append(TemporalChange(
                    obj=overlap,
                    action="trim_left",
                    old_start=overlap.start_date,
                    old_end=overlap.end_date,
                    new_start=instance.end_date + datetime.timedelta(days=1),
                    new_end=overlap.end_date,
                ))

        return changes

    def create_temporal(self, **kwargs):
        instance = self.model(**kwargs)
        clashes = self.analyze_clashes(instance)
        if clashes:
            raise ValidationError("Temporal conflict detected")
        instance.save()
        return instance

    def active_at(self, date=None):
        date = date or datetime.date.today()
        return self.filter(
            start_date__lte=date
        ).filter(
            Q(end_date__isnull=True) |
            Q(end_date__gte=date)
        )

    def history_for(self, **kwargs):
        qs = self
        for field, value in kwargs.items():
            qs = qs.filter(**{field: value})
        return qs.order_by("-start_date")

class TemporalManager(models.Manager):
    def get_queryset(self):
        return TemporalQuerySet(self.model, using=self._db)

    def analyze_clashes(self, instance):
        return self.get_queryset().analyze_clashes(instance)

    def resolve_by_trimming(self, instance):
        with transaction.atomic():
            changes = self.analyze_clashes(instance)

            for change in changes:
                obj = self.get_queryset().select_for_update().get(pk=change.obj.pk)

                if change.action == "delete":
                    obj.delete()

                elif change.action == "trim_right":
                    obj.end_date = change.new_end
                    obj.save(update_fields=["end_date"])

                elif change.action == "trim_left":
                    obj.start_date = change.new_start
                    obj.save(update_fields=["start_date"])

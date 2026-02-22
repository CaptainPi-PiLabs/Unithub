import datetime
from dataclasses import dataclass
from typing import Optional

from django.db import models, transaction


@dataclass
class TemporalChange:
    obj: models.Model
    action: str  # "delete", "trim_left", "trim_right"
    old_start: Optional[datetime.date]
    old_end: Optional[datetime.date]
    new_start: Optional[datetime.date]
    new_end: Optional[datetime.date]

class TemporalQuerySet(models.QuerySet):
    def overlapping_for(self, instance):
        return instance.get_overlap_queryset()

    def analyze_clashes(self, instance):
        """
            Returns a list describing what WOULD change if this entry were applied.
            Does not modify the database.
            """
        print("ANALYZE CLASHES", instance.start_date, instance.end_date)
        changes = []
        overlaps = instance.get_overlap_queryset().order_by("start_date")

        for overlap in overlaps:
            print("Overlap: ", overlap)
            print("Target dates: ", overlap.start_date, overlap.end_date)
            # Fully enclosed → delete
            if (
                    instance.start_date <= overlap.start_date and
                    (
                            instance.end_date is None or
                            (
                                    overlap.end_date is not None and
                                    overlap.end_date <= instance.end_date
                            )
                    )
            ):
                print("Overlap was fulling enclosed")
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
            if overlap.start_date < instance.start_date:
                print("Trimming overlap to the right")
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
            if (
                    instance.end_date is not None and
                    (
                            overlap.end_date is None or
                            overlap.end_date > instance.end_date
                    )
            ):
                print("Trimming overlap to the left")
                changes.append(TemporalChange(
                    obj=overlap,
                    action="trim_left",
                    old_start=overlap.start_date,
                    old_end=overlap.end_date,
                    new_start=instance.end_date + datetime.timedelta(days=1),
                    new_end=overlap.end_date,
                ))

        return changes

class TemporalManager(models.Manager):
    def get_queryset(self):
        return TemporalQuerySet(self.model, using=self._db)

    def analyze_clashes(self, instance):
        return self.get_queryset().analyze_clashes(instance)

    def resolve_by_trimming(self, instance):
        with transaction.atomic():
            changes = self.analyze_clashes(instance)

            for change in changes:
                obj = change.obj

                if change.action == "delete":
                    obj.delete()

                elif change.action == "trim_right":
                    obj.end_date = change.new_end
                    obj.save(update_fields=["end_date"])

                elif change.action == "trim_left":
                    obj.start_date = change.new_start
                    obj.save(update_fields=["start_date"])

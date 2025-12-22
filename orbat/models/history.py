import datetime

from django.conf import settings
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone

from orbat.models import Section, Role
from users.models import UserStatus


class BaseHistoryModel(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    non_overlapping_fields = []

    class Meta:
        abstract = True
        ordering = ['-start_date']

    def is_active(self, date=None):
        if date is None:
            date = timezone.now().date()
        return self.start_date <= date and (self.end_date is None or self.end_date >= date)

    def _delete_if_zero_length(self):
        if self.end_date and self.start_date == self.end_date:
            # Instead of storing pointless same-day range, just delete
            if self.pk:
                self.delete()
            return True
        return False

    def save(self, *args, **kwargs):
        from django.db import transaction
        from django.db.models import Q
        import datetime

        if self._delete_if_zero_length():
            return

        with transaction.atomic():
            if not self.non_overlapping_fields:
                # EXCLUSIVE timeline
                # Deduplicate same-day
                existing = (
                    self.__class__.objects
                    .filter(user=self.user, start_date=self.start_date)
                    .exclude(pk=self.pk)
                    .first()
                )
                if existing:
                    # Overwrite fields
                    for field in self._meta.fields:
                        if field.name not in {"id", "created_at", "updated_at", "user", "start_date"}:
                            setattr(existing, field.name, getattr(self, field.name))
                    existing.save()
                    return existing

            # Determine filter for non-overlapping fields
            filters = Q(user=self.user)
            for field in getattr(self, "non_overlapping_fields", []):
                filters &= Q(**{field: getattr(self, field)})

            overlaps = (
                self.__class__.objects
                .filter(filters)
                .exclude(pk=self.pk)
                .filter(
                    Q(end_date__isnull=True, start_date__lte=self.end_date or self.start_date) |
                    Q(start_date__lte=self.end_date or self.start_date, end_date__gte=self.start_date)
                )
                .order_by("start_date")
            )

            for overlap in overlaps:
                # Fully replaced? delete
                if self.start_date <= overlap.start_date and (self.end_date is None or overlap.end_date <= self.end_date):
                    overlap.delete()
                else:
                    # Trim overlaps
                    if overlap.start_date < self.start_date <= (overlap.end_date or self.start_date):
                        overlap.end_date = self.start_date - datetime.timedelta(days=1)
                        overlap.save(update_fields=["end_date"])
                    if self.end_date and (self.start_date <= overlap.start_date <= self.end_date):
                        overlap.start_date = self.end_date + datetime.timedelta(days=1)
                        overlap.save(update_fields=["start_date"])

            return super().save(*args, **kwargs)


class HistorySectionAssignment(BaseHistoryModel):
    section = models.ForeignKey(Section, on_delete=models.CASCADE)

class HistoryRoleAssignment(BaseHistoryModel):
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    role_name_at_assignment = models.CharField(max_length=50, blank=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)

    non_overlapping_fields = ["role"]  # ensures same role does not overlap

class HistoryUsername(BaseHistoryModel):
    username = models.CharField(max_length=50)

class HistoryUserStatus(BaseHistoryModel):
    status = models.CharField(max_length=20, choices=UserStatus.choices)

    def __str__(self):
        return f"{self.user.display_name} - {self.get_status_display()} - {self.start_date} to {self.end_date or "present}"})"


def get_section_on_date(user, date):
    assignment = (
        HistorySectionAssignment.objects
        .select_related("section")
        .filter(user=user, start_date__lte=date)
        .filter(Q(end_date__isnull=True) | Q(end_date__gte=date))
        .first()
    )
    return assignment.section if assignment else None


def get_display_name_on_date(user, date):
    name_record = (
        HistoryUsername.objects
        .filter(user=user, start_date__lte=date)
        .filter(Q(end_date__isnull=True) | Q(end_date__gte=date))
        .first()
    )

    display_name = name_record.display_name if name_record else user.display_name

    section = get_section_on_date(user, date.date())
    section_shorthand = getattr(section, "shorthand", None)

    return f"[{section_shorthand}] {display_name}" if section_shorthand else display_name
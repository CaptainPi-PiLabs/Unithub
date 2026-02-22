from django.conf import settings
from django.db import models
from django.utils import timezone
from django.db.models import Q
from django.core.exceptions import ValidationError
import datetime


class TemporalRange(models.Model):
    """
    Generic non-overlapping date-range history model.

    Rules:
    - start_date is inclusive
    - end_date is inclusive
    - end_date = NULL means 'present'
    """

    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Optional: restrict overlap scope (e.g. per slot, per role)
    non_overlapping_fields = []

    class Meta:
        abstract = True
        ordering = ["-start_date"]

    def is_active(self, date=None):
        if date is None:
            date = timezone.now().date()
        return (
            self.start_date <= date and
            (self.end_date is None or self.end_date >= date)
        )

    def clean(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError("end_date cannot be before start_date")

    def save(self, *args, **kwargs):
        from django.db import transaction

        if self.start_date is None:
            self.start_date = timezone.now().date()

        self.full_clean()

        return super().save(*args, **kwargs)

    def get_overlap_queryset(self, *, start_date=None, end_date=None):
        """
        Returns queryset of overlapping rows (excluding self).
        """
        start = start_date or self.start_date
        end = end_date if end_date is not None else self.end_date

        filters = Q()
        for field in self.non_overlapping_fields:
            value = getattr(self, field)
            if value is None:
                filters &= Q(**{f"{field}__isnull": True})
            else:
                filters &= Q(**{field: value})

        qs = self.__class__.objects.filter(filters).exclude(pk=self.pk)

        if end:
            return qs.filter(
                Q(end_date__isnull=True, start_date__lte=end) |
                Q(start_date__lte=end, end_date__gte=start)
            )
        else:
            return qs.filter(
                Q(end_date__isnull=True) |
                Q(end_date__gte=start)
            )

    def check_for_clashes(self):
        return self.get_overlap_queryset()

class ApplicationBase(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_DENIED = "denied"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_DENIED, "Denied"),
    ]

    date = models.DateTimeField(default=timezone.now)
    processed_date = models.DateTimeField(null=True, blank=True)
    actioned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_actioned"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    comment = models.TextField(blank=True)
    closed = models.BooleanField(default=False)

    class Meta:
        abstract = True
        ordering = ["-date"]

    def approve(self, actioned_by=None):
        self.status = self.STATUS_APPROVED
        self.actioned_by = actioned_by or self.actioned_by
        self.processed_date = timezone.now()
        self.closed = True
        self.save(update_fields=["status", "actioned_by", "processed_date", "closed"])

    def deny(self, actioned_by=None):
        self.status = self.STATUS_DENIED
        self.actioned_by = actioned_by or self.actioned_by
        self.processed_date = timezone.now()
        self.closed = True
        self.save(update_fields=["status", "actioned_by", "processed_date", "closed"])

    @property
    def is_pending(self):
        return self.status == self.STATUS_PENDING

    @property
    def is_approved(self):
        return self.status == self.STATUS_APPROVED

    @property
    def is_denied(self):
        return self.status == self.STATUS_DENIED

    @property
    def is_open(self):
        return not self.closed
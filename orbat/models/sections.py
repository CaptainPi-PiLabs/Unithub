from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q, Max
from django.utils import timezone
from django.utils.text import slugify

from common.mixins.model_mixin import OrderedModelMixin
from common.temporal.managers import TemporalManager
from common.temporal.models import TemporalRange, ApplicationBase


class Platoon(OrderedModelMixin, models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Section(OrderedModelMixin, models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    shorthand = models.CharField(max_length=10)
    description = models.TextField(blank=True)
    max_size = models.IntegerField()
    platoon = models.ForeignKey(Platoon, null=True, blank=True, related_name='sections', on_delete=models.SET_NULL)

    _order_scope_fields = ["platoon"]
    class Meta:
        ordering = ["platoon", "order"]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        self.slug = slugify(self.name)

        qs = Section.objects.exclude(pk=self.pk).filter(slug=self.slug)
        if qs.exists():
            raise ValidationError({
                "name": "This name conflicts with an existing section."
            })

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if is_new:
            last_order = (
                Section.objects
                .filter(platoon=self.platoon)
                .aggregate(max_order=Max("order"))["max_order"]
            )
            self.order = (last_order or 0) + 1

        self.full_clean()
        super().save(*args, **kwargs)

class SectionSlot(OrderedModelMixin, models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="slots")
    is_leader = models.BooleanField(default=False)

    _details_cache = None
    _cache_datetime = None

    _order_scope_fields = ["section"]

    class Meta:
        ordering = ["order", "section"]

    def __str__(self):
        return f"{self.section} - {self.get_name()}"

    def delete(self, *args, **kwargs):
        if self.is_leader:
            raise ValueError("Cannot delete the Section Leader slot.")
        super().delete(*args, **kwargs)

    def get_name(self, date=None):
        details = self.get_details_at(date)
        return details.name if details else None

    def get_colour(self, date=None):
        details = self.get_details_at(date)
        return details.colour if details else None

    def is_officer(self, date=None):
        details = self.get_details_at(date)
        return details.is_officer if details else False

    def get_details_at(self, date=None):
        """
        Returns the SectionSlotDetail active at the given date.
        Caches the result for the requested date.
        """
        if date is None:
            date = timezone.now().date()

        # check cache
        if self._details_cache is not None and self._cache_datetime == date:
            return self._details_cache

        # query for details
        details = (
            self.details
            .filter(start_date__lte=date)
            .filter(Q(end_date__isnull=True) | Q(end_date__gte=date))
            .order_by("-start_date")
            .first()
        )

        # update cache
        self._details_cache = details
        self._cache_datetime = date

        return details

    def get_assignment_at(self, date=None):
        if date is None:
            date = timezone.now().date()

        return (
            self.assignments
            .filter(start_date__lte=date)
            .filter(Q(end_date__isnull=True) | Q(end_date__gte=date))
            .order_by("-start_date")
            .first()
        )

    def current_user(self):
        assignment = self.get_assignment_at()
        return assignment.user if assignment else None

    current_user.short_description = "Current User"

class SectionSlotDetail(TemporalRange):
    slot = models.ForeignKey(SectionSlot, on_delete=models.CASCADE, related_name='details')
    name = models.CharField(max_length=50)
    colour = models.CharField(
        max_length=10,
        choices=[
            ("Gold", "Gold"),
            ("Green", "Green"),
            ("Red", "Red"),
            ("Blue", "Blue"),
        ],
        null=True,
        blank=True,
    )

    is_officer = models.BooleanField(default=False)

    objects = TemporalManager()
    non_overlapping_fields = ["slot"]

    def __str__(self):
        return f"{self.slot.section} – {self.name}"

    def get_history_at(self, dt=None):
        if dt is None:
            dt = timezone.now()
        return (
            self.history_set
            .filter(start_date__lte=dt)
            .filter(Q(end_date__isnull=True) | Q(end_date__gte=dt))
            .first()
        )

class SectionSlotAssignment(TemporalRange):
    slot = models.ForeignKey(
        SectionSlot,
        related_name="assignments",
        on_delete=models.CASCADE
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="slot_assignments",
        on_delete=models.CASCADE
    )
    first_joined = models.DateTimeField()

    non_overlapping_fields = ["slot", "user"]

    objects = TemporalManager()

    class Meta(TemporalRange.Meta):
        constraints = [
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(end_date__isnull=True),
                name="user_single_active_slot",
            )
        ]

    def save(self, *args, **kwargs):
        self._is_new_section_join = False

        if self._state.adding and not self.first_joined:
            now = timezone.now()

            previous = (
                SectionSlotAssignment.objects
                .filter(user=self.user)
                .exclude(pk=self.pk)
                .order_by("-start_date")
                .first()
            )

            if (
                previous
                and previous.end_date is not None
                and previous.slot.section_id == self.slot.section_id
            ):
                # internal move
                self.first_joined = previous.first_joined
            else:
                # New section join
                self.first_joined = now
                self._is_new_section_join = True

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.slot}: {self.user}"

class SectionApplication(ApplicationBase):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="section_applications")
    section_slot = models.ForeignKey(SectionSlot, on_delete=models.CASCADE)

    def __str__(self):
        history = self.section_slot.get_history_at(self.date)
        name = history.name if history else self.section_slot.pk
        return f"{self.section_slot.section} - {name}: {self.user.display_name}"
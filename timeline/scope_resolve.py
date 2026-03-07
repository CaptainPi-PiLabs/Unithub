from collections import defaultdict

from django.db.models import Q

from orbat.models.sections import SectionSlotAssignment
from users.models import UnitMembership


class ScopeResolver:
    def __init__(self, user=None, section=None, start_date=None, end_date=None):
        self.user = user
        self.section = section
        self.start_date = start_date
        self.end_date = end_date

        self._section_assignments = None
        self._unit_memberships = None

    def _load_section_assignments(self):
        if self._section_assignments is not None:
            return self._section_assignments

        qs = SectionSlotAssignment.objects.select_related(
            "user",
            "slot",
            "slot__section"
        )

        if self.section:
            qs = qs.filter(slot__section=self.section)

        if self.start_date:
            qs = qs.filter(
                Q(end_date__isnull=True) | Q(end_date__gte=self.start_date)
            )
        if self.end_date:
            qs = qs.filter(start_date__lte=self.end_date)

        index = defaultdict(list)

        for assignment in qs:
            index[assignment.user_id].append(assignment)

        self._section_assignments = index
        return self._section_assignments

    def _load_unit_memberships(self):
        if self._unit_memberships is not None:
            return self._unit_memberships

        qs = UnitMembership.objects.select_related("user")
        if self.start_date:
            qs = qs.filter(
                Q(end_date__isnull=True) | Q(end_date__gte=self.start_date)
            )
        if self.end_date:
            qs = qs.filter(start_date__lte=self.end_date)

        self._unit_memberships = list(qs)
        return self._unit_memberships

    def user_in_section(self, user, dt):
        if user is None:
            user = self.user
        if user is None or dt is None:
            return False

        for assignment in self._load_section_assignments().get(user.id, []):
            if assignment.start_date <= dt and (
                assignment.end_date is None or assignment.end_date >= dt
            ):
                return True
        return False

    def date_bound_check(self, date_field):
        if self.start_date and date_field < self.start_date:
            return False
        if self.end_date and date_field > self.end_date:
            return False
        return True

    def resolve(self, date_field, user=None):
        if not self.date_bound_check(date_field):
            return False
        if self.section:
            return self.user_in_section(user, date_field)
        return True

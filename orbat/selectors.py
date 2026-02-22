from django.db.models import Q
from django.utils import timezone

from orbat.models.sections import SectionSlotAssignment


def get_section_slot(user, date = None):
    if date is None:
        date = timezone.now().date()

    assignment = (
        SectionSlotAssignment.objects
        .filter(
            user=user,
            start_date__lte=date,
        )
        .filter(
            Q(end_date__isnull=True) | Q(end_date__gte=date)
        )
        .order_by("-start_date")
        .first()
    )

    return assignment.slot if assignment else None

def is_user_in_section(user, section=None, date=None) -> bool:
    slot = get_section_slot(user, date)

    if not slot:
        return False
    if section is None:
        return True

    return slot.section_id == section.id
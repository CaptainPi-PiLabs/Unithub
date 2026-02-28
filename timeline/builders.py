from django.db.models import Q

from orbat.models.sections import SectionSlotAssignment, SectionSlotDetail
from timeline.events import TimelineEvent
from timeline.models import TimelineTypes


def apply_date_filters(qs, field_name, start_date=None, end_date=None):
    filters = {}

    if start_date:
        filters[f"{field_name}__gte"] = start_date

    if end_date:
        filters[f"{field_name}__lte"] = end_date

    return qs.filter(**filters)

def get_unit_history(user=None, section=None, start_date=None, end_date=None):
    pass

def get_assignment_history(user=None, section=None, start_date=None, end_date=None):
    qs = SectionSlotAssignment.objects.select_related(
        "user",
        "slot",
        "slot__section"
    )
    if user:
        qs = qs.filter(user=user)

    if section:
        qs = qs.filter(slot__section=section)

    if start_date:
        qs = qs.filter(
            Q(end_date__isnull=True) | Q(end_date__gte=start_date)
        )
    if end_date:
        qs = qs.filter(start_date__lte=end_date)

    events = []

    for assignment in qs:
        event_type = (
            TimelineTypes.SECTION_JOINED
            if assignment.first_joined == assignment.start_date
            else TimelineTypes.ROLE_ASSIGNED
        )

        events.append(
            TimelineEvent(
                event_type=event_type,
                timestamp=assignment.start_date,
                user=assignment.user,
                section=assignment.slot.section,
                snapshot_name=assignment.slot.get_name(date=assignment.start_date),
                source=assignment.slot,
            )
        )
        #  TODO Get if assignment has no next neighbour. Left Section

        details = SectionSlotDetail.objects.filter(
            slot=assignment.slot,
            start_time__gt=assignment.start_date,
        )
        if assignment.end_date:
            details = details.filter(start_time__lt=assignment.end_date)

        for detail in details:
            events.append(
                TimelineEvent(
                    event_type=TimelineTypes.ROLE_ASSIGNED,
                    timestamp=detail.start_time,
                    user=assignment.user,
                    section=assignment.slot.section,
                    snapshot_name=detail.name,
                    source=assignment.slot,
                )
            )

    return sorted(events, key=lambda e: e.timestamp, reverse=True)


def get_training_history(user=None, section=None, start_date=None, end_date=None, qualification=None):
    pass

def get_award_history(user=None, section=None, start_date=None, end_date=None, award=None):
    pass
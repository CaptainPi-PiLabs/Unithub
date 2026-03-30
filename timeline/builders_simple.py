from datetime import timedelta

from orbat.models.sections import SectionSlotAssignment
from timeline.events import TimelineEvent
from timeline.models import TimelineTypes


def build_unit_events(qs, scope):
    events = []

    for membership in qs:
        user = membership.user

        if scope.resolve(membership.start_date, user):
            events.append(
                TimelineEvent(
                    event_type=TimelineTypes.UNIT_JOINED,
                    timestamp=membership.start_date,
                    user=user,
                    source=membership,
                )
            )

        if membership.end_date and scope.resolve(membership.end_date, user):
            events.append(
                TimelineEvent(
                    event_type=TimelineTypes.UNIT_LEFT,
                    timestamp=membership.end_date,
                    user=user,
                    source=membership,
                )
            )

        for promotion in membership.promotions.all():
            if scope.resolve(promotion.date_awarded, user):
                events.append(
                    TimelineEvent(
                        event_type=TimelineTypes.MEMBERSHIP_TIER_CHANGED,
                        timestamp=promotion.date_awarded,
                        user=user,
                        source=promotion,
                    )
                )

    return events

def build_assignment_events(qs, scope):
    events = []

    for assignment in qs:
        user = assignment.user

        if scope.resolve(assignment.start_date, user):
            events.append(
                TimelineEvent(
                    event_type=TimelineTypes.SECTION_JOINED,
                    timestamp=assignment.start_date,
                    user=user,
                    section=assignment.slot.section,
                    snapshot_name=assignment.slot.get_name(
                        date=assignment.start_date
                    ),
                    source=assignment.slot,
                )
            )

        if assignment.end_date and scope.resolve(assignment.end_date, user):
            # TODO Use prefetched QS. Currently very unoptimised. Can use the current assignment queryset but a check will need to be done for the next day from the DB if assignment end_date matches scope end_date as the next day won't be included
            tomorrow = assignment.end_date + timedelta(days=1)
            if not SectionSlotAssignment.objects.filter(user=assignment.user, slot__section=assignment.slot.section, start_date=tomorrow).exists():
                events.append(
                    TimelineEvent(
                        event_type=TimelineTypes.SECTION_LEFT,
                        timestamp=assignment.end_date,
                        user=user,
                        section=assignment.slot.section,
                        source=assignment.slot,
                    )
                )

    return events

def build_training_events(qs, scope):
    events = []

    for qualification in qs:
        user = qualification.user

        if scope.resolve(qualification.date_awarded, user):
            events.append(
                TimelineEvent(
                    event_type=TimelineTypes.TRAINING_COMPLETED,
                    timestamp=qualification.date_awarded,
                    user=user,
                    section=qualification.section,
                    snapshot_name=qualification.qualification.name,
                    source=qualification.qualification,
                )
            )

    return events
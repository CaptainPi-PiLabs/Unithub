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
import heapq
from collections import OrderedDict
from datetime import timedelta

from django.db.models import Q
from orbat.models.sections import SectionSlotAssignment
from timeline.builders_simple import build_unit_events, build_assignment_events, build_training_events
from timeline.events import TimelineEvent
from timeline.models import TimelineTypes
from timeline.scope_resolve import ScopeResolver
from training.models import UserQualification
from users.models import UnitMembership

def build_timeline(streams):
    return list(merge_event_streams(*streams))

def merge_event_streams(*streams):
    heap = []

    for stream_id, stream in enumerate(streams):
        stream = iter(stream)
        try:
            event = next(stream)
            heapq.heappush(
                heap,
                (-event.timestamp.timestamp(), stream_id, event, stream)
            )
        except StopIteration:
            pass

    while heap:
        _, stream_id, event, stream = heapq.heappop(heap)

        yield event

        try:
            next_event = next(stream)
            heapq.heappush(
                heap,
                (-next_event.timestamp.timestamp(), stream_id, next_event, stream)
            )
        except StopIteration:
            pass

def unit_history_stream(qs, scope):
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

        for rank in membership.promotions.all():
            if scope.resolve(rank.date_awarded, user):
                events.append(
                    TimelineEvent(
                        event_type=TimelineTypes.MEMBERSHIP_TIER_CHANGED,
                        timestamp=rank.date_awarded,
                        user=user,
                        source=rank,
                    )
                )

    events.sort(key=lambda e: e.timestamp, reverse=True)

    for event in events:
        yield event

def get_unit_timeline(user=None, section=None, start_date=None, end_date=None):
    scope = ScopeResolver(user, section, start_date, end_date)

    qs = UnitMembership.objects.select_related("user").prefetch_related("ranks")

    if user:
        qs = qs.filter(user=user)

    if start_date:
        qs = qs.filter(
            Q(end_date__isnull=True) | Q(end_date__gte=start_date)
        )
    if end_date:
        qs = qs.filter(start_date__lte=end_date)

    unit_stream = unit_history_stream(qs, scope)
    return list(unit_stream)

def assignment_history_stream(qs, scope):
    qs = qs.order_by("-start_date")
    for assignment in qs:
        if scope.resolve(assignment.start_date, assignment.user):
            if scope.user_in_section(assignment.user, assignment.end_date):
                event_type = TimelineTypes.ROLE_ASSIGNED
            else:
                event_type = TimelineTypes.UNIT_JOINED

            yield TimelineEvent(
                event_type=event_type,
                timestamp=assignment.start_date,
                user=assignment.user,
                section=assignment.slot.section,
                snapshot_name=assignment.slot.get_name(date=assignment.start_date),
                source=assignment.slot,
            )
            if assignment.end_date and scope.resolve(assignment.end_date + timedelta(days=1), assignment.user):
                yield TimelineEvent(
                    event_type=TimelineTypes.SECTION_LEFT,
                    timestamp=assignment.end_date,
                    user=assignment.user,
                    section=assignment.section,
                    source=assignment.slot,
                )

def get_assignment_timeline(user=None, section=None, start_date=None, end_date=None):
    scope = ScopeResolver(user, section, start_date, end_date)
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

    assignment_stream = assignment_history_stream(qs, scope)
    return list(assignment_stream)

def training_history_steam(qs, scope):
    qs = qs.order_by("-date_awarded")
    for user_qual in qs:
        if scope.resolve(user_qual.date_awarded, user_qual.user):
            yield TimelineEvent(
                event_type=TimelineTypes.TRAINING_COMPLETED,
                timestamp=user_qual.date_awarded,
                user=user_qual.user,
                section=user_qual.section,
                snapshot_name=user_qual.qualification.name,
                source=user_qual.qualification,
            )

def get_training_timeline(user=None, section=None, start_date=None, end_date=None, qualification=None):
    scope = ScopeResolver(user, section, start_date, end_date)

    qs = UserQualification.objects.select_related("user").prefetch_related("qualification")

    if user:
        qs = qs.filter(user=user)
    if qualification:
        qs = qs.filter(qualification=qualification)
    if start_date:
        qs = qs.filter(date_awarded__gte=start_date)
    if end_date:
        qs = qs.filter(date_awarded__lte=end_date)

    events = []
    events.extend(build_training_events(qs, scope))
    events.sort(key=lambda e: e.timestamp, reverse=True)

    return events


def get_orbat_timeline(user=None, section=None, start_date=None, end_date=None):
    scope = ScopeResolver(user, section, start_date, end_date)

    qs = SectionSlotAssignment.objects

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

    events.extend(build_assignment_events(qs, scope))
    events.sort(key=lambda e: e.timestamp, reverse=True)

    return events

def get_personal_timeline(user, start_date=None, end_date=None):
    scope = ScopeResolver(user, start_date=start_date, end_date=end_date)

    unit_qs = UnitMembership.objects.filter(user=user).prefetch_related("promotions")
    assignment_qs = SectionSlotAssignment.objects.filter(user=user).prefetch_related("slot", "slot__section")
    # training_qs = UserQualification.objects.filter(user=user).prefetch_related("qualification")

    events = []

    events.extend(build_unit_events(unit_qs, scope))
    events.extend(build_assignment_events(assignment_qs, scope))
    # events.extend(build_training_events(training_qs, scope))

    events.sort(key=lambda e: e.timestamp, reverse=True)

    return events


def group_timeline_entries(events):
    grouped = OrderedDict()

    for event in events:
        timestamp = event.get("timestamp")
        if not timestamp:
            continue

        grouped.setdefault(timestamp, []).append(event)

    return grouped.items()
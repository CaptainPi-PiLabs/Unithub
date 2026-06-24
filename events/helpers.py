from datetime import datetime, timedelta, date

from events.models import Event, EventRole, EventAssignment, EventGroup


def create_training_event(
    qualification,
    organizer,
    event_date,
    start_time,
    attendees=None,
    duration_hours=1,
):
    end_time = (
        datetime.combine(date.today(), start_time)
        + timedelta(hours=duration_hours)
    ).time()

    event = Event.objects.create(
        name=f"{qualification.name} - {event_date}",
        qualification=qualification,
        date=event_date,
        start_time=start_time,
        end_time=end_time,
        type="TR",
    )

    EventRole.objects.create(
        event=event,
        user=organizer,
        role="ORGANIZER",
    )

    instructor_group = EventGroup.objects.create(event=event, name=EventGroup.INSTRUCTOR)
    EventGroup.objects.create(event=event, name=EventGroup.HELPERS)
    EventGroup.objects.create(event=event, name=EventGroup.TRAINEES)

    EventAssignment.objects.create(
        event=event,
        user=organizer,
        event_group=instructor_group,
        assigned_by=organizer,
    )

    if attendees:
        EventAssignment.objects.bulk_create(
            [
                EventAssignment(
                    event=event,
                    user=user,
                )
                for user in attendees
            ]
        )

    return event
import datetime

from django.db import models
from django.utils import timezone

from attendance.models import Attendance
from events.models import Event


class AttendanceManager(models.Manager):
    def mark_user_join(self, user, timestamp=None):
        if timestamp is None:
            timestamp = timezone.now()
        today_events = Event.objects.filter(date=timestamp.date())
        for event in today_events:
            attendance, created = Attendance.objects.get_or_create(
                event=event,
                user=user,
                defaults={"first_join": timestamp, "last_seen": timestamp}
            )
            if not created:
                # Already present, maybe reconnecting mid-event
                if timestamp < attendance.first_join:
                    attendance.first_join = timestamp
                if timestamp > attendance.last_seen:
                    attendance.last_seen = timestamp
                attendance.save()

    def mark_user_leave(self, user, timestamp=None):
        if timestamp is None:
            timestamp = timezone.now()
        today_events = Event.objects.filter(date=timestamp.date())
        for event in today_events:
            try:
                attendance = Attendance.objects.get(event=event, user=user)
            except Attendance.DoesNotExist:
                continue

            if timestamp < datetime.datetime.combine(event.date, event.start_time, tzinfo=timezone.utc):
                # Left before event started
                attendance.delete()
            else:
                attendance.last_seen = timestamp
                if timestamp < datetime.datetime.combine(event.date, event.end_time, tzinfo=timezone.utc):
                    attendance.left_early = True
                attendance.save()

    def mark_manual_attendance(self, user, event, first_join=None, last_seen=None):
        """
        Create or update an attendance entry manually.
        If times are not provided, they are left blank (optional).
        """
        attendance, created = Attendance.objects.get_or_create(
            event=event,
            user=user,
            defaults={
                "first_join": first_join,
                "last_seen": last_seen,
                "manual": True,
                "left_early": False,
            },
        )
        if not created:
            # Update existing manual entry
            if first_join:
                attendance.first_join = first_join
            if last_seen:
                attendance.last_seen = last_seen
            attendance.manual = True  # Ensure it's marked manual
            attendance.save()
        return attendance

    def cleanup_pre_event_entries(self, server_start_time=None):
        """
        Delete attendance entries for events that haven't started yet.
        """
        if server_start_time is None:
            server_start_time = timezone.now()

        # Get all events today that haven't started yet
        events_to_cleanup = Event.objects.filter(
            date=server_start_time.date(),
            start_time__gt=server_start_time.time()
        )

        # Delete any attendance entries for those events
        self.filter(event__in=events_to_cleanup).delete()
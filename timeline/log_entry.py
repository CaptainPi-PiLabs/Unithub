from timeline.models import TimelineTypes
from timeline.utils import add_entry


def log_assignment_change(user, action, source, obj):
    if source == "SectionSlotAssignment":
        section = obj.slot.section if obj.slot else None

        if action == "added":
            add_entry(
                event_type=TimelineTypes.SECTION_JOINED,
                user=user,
                section=section,
                snapshot_name=obj.slot.get_name(),
                related_object=obj,
            )

        elif action == "removed":
            add_entry(
                event_type=TimelineTypes.SECTION_LEFT,
                user=user,
                section=section,
                snapshot_name=obj.slot.get_name(),
                related_object=obj,
            )
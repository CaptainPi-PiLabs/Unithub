from django.urls import reverse

from timeline.models import TimelineTypes


def _build_event_message(event, section_meta):

    if event.event_type == TimelineTypes.SECTION_JOINED:
        message = f"Joined {section_meta['name']}"
        if event.snapshot_name:
            message = message + f" as {event.snapshot_name}"

    elif event.event_type == TimelineTypes.SECTION_LEFT:
        message = f"Left {section_meta['name']}"

    elif event.event_type == TimelineTypes.UNIT_JOINED:
        message = "Joined the unit"

    elif event.event_type == TimelineTypes.UNIT_LEFT:
        message = "Left the unit"

    elif event.event_type == TimelineTypes.TRAINING_COMPLETED:
        message = f"Completed {event.snapshot_name}"
    else:
        message = str(event.event_type.label)

    return message

def build_timeline_display_entries(events):
    user_cache = {}
    section_cache = {}

    display_entries = []

    for event in events:
        user = event.user

        if user.id not in user_cache:
            discord = getattr(user, "discordaccount", None)

            user_cache[user.id] = {
                "display_name": user.display_name,
                "profile_url": "#",
                "avatar_url": (
                    discord.avatar_url if discord else None,
                )
            }

        user_meta = user_cache[user.id]

        section_meta = None
        if getattr(event, "section", None):
            section = event.section

            if section.id not in section_cache:
                section_cache[section.id] = {
                    "name": str(section),
                    "url": (
                        section.get_absolute_url()
                        if hasattr(section, "get_absolute_url")
                        else reverse(
                            "orbat_section_detail",
                            args=[section.slug]
                        )
                    ),
                }

            section_meta = section_cache[section.id]

        display_entries.append({
            "timestamp": event.timestamp,
            "event_type": event.event_type.label,
            "message": _build_event_message(event, section_meta),
            "user": user_meta,
            "section": section_meta,
            "source": event.source,
        })

    return display_entries
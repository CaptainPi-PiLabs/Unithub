from django.core.management.base import BaseCommand
from django.core.exceptions import ValidationError

from intergrations.events import EventType
from intergrations.services import publish

"""
examples

python manage.py publish_event member_approved --payload '{"user_id":"4c5e7d8a-1234-5678-9abc-def012345678"}'

python manage.py publish_event discord_sync --payload '{"guild_id":123456789,"force":true}'

"""


class Command(BaseCommand):
    help = "Publish an integration event"

    def add_arguments(self, parser):
        parser.add_argument("event_type")
        parser.add_argument(
            "--payload",
            default="{}",
            help='JSON payload (e.g. \'{"user_id": "123"}\')',
        )

    def handle(self, *args, **options):
        import json

        event_type = options["event_type"]

        try:
            EventType(event_type)
        except ValueError:
            raise ValidationError(f"Unknown event type: {event_type}")

        payload = json.loads(options["payload"])

        event = publish(event_type, **payload)

        self.stdout.write(
            self.style.SUCCESS(
                f"Published event {event.id} ({event.event_type})"
            )
        )
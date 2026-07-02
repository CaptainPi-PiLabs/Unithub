from uuid import UUID

from redis.exceptions import RedisError

from .models import IntegrationEvent
from .redis_utils import get_redis_client

STREAM_NAME = "integration-events"

def normalise(value):
    if isinstance(value, UUID):
        return str(value)
    return value

def publish(event_type, **payload):
    payload = {
        key: normalise(value)
        for key, value in payload.items()
    }

    event = IntegrationEvent.objects.create(event_type=event_type, payload=payload)
    publish_to_redis(event)
    return event

def publish_to_redis(event):
    redis = get_redis_client()
    if redis is None:
        return

    try:
        redis.xadd(
            STREAM_NAME,
            {
                "event_id": str(event.pk),
                "event_type": event.event_type,
            },
        )
        event.status = IntegrationEvent.Status.PUBLISHED
        event.error = ""
    except RedisError as exc:
        event.status = IntegrationEvent.Status.ERRORED
        event.error = str(exc)

    event.save(update_fields=["status", "error"])
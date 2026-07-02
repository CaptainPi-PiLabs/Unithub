from django.conf import settings
import redis

_redis_client = None

def get_redis_client():
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    if not settings.REDIS_URL:
        return None

    _redis_client = redis.Redis.from_url(
        settings.REDIS_URL,
        protocol=settings.REDIS_PROTOCOL
    )
    return _redis_client
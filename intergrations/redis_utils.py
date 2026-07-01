from django.conf import settings
import redis

_client = None

def get_redis_client():
    global _client
    if _client is not None:
        return _client

    if not settings.REDIS_URL:
        return None

    _client = redis.Redis.from_url(settings.REDIS_URL)
    return _client
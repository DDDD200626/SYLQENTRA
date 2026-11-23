from app.core.config import settings


def check_redis() -> str:
    if not settings.REDIS_URL:
        return "disabled"
    try:
        import redis

        client = redis.Redis.from_url(settings.REDIS_URL, socket_connect_timeout=0.5, socket_timeout=0.5)
        client.ping()
        return "ok"
    except Exception:
        return "unavailable"

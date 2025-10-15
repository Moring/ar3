import sys
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

try:
    import redis
except ImportError as exc:
    redis = None
    IMPORT_ERROR = exc
else:
    IMPORT_ERROR = None


class Command(BaseCommand):
    help = "Verifies the configured Huey Redis instance is reachable."

    def handle(self, *args, **options):
        if redis is None:
            raise CommandError(f"redis package unavailable: {IMPORT_ERROR}")  # pragma: no cover

        huey_config = getattr(settings, "HUEY", {})
        redis_url = huey_config.get("connection", {}).get("url")

        if not redis_url:
            raise CommandError("Huey Redis URL is not configured (settings.HUEY['connection']['url']).")
        if huey_config.get("immediate"):
            self.stdout.write(self.style.SUCCESS("redis-ok (immediate mode)"))
            return 0

        client = redis.Redis.from_url(redis_url)
        try:
            client.ping()
        except redis.ConnectionError as exc:
            raise CommandError(f"Could not reach Redis at {redis_url}: {exc}") from exc

        self.stdout.write(self.style.SUCCESS("redis-ok"))
        return 0

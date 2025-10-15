from pathlib import Path
from django.conf import settings


def client_media_path(client) -> Path:
    """Return the directory for the client's media bucket."""
    return Path(settings.MEDIA_ROOT) / client.slug


def ensure_client_media_path(client) -> Path:
    """
    Make sure the client's media directory exists so uploads have a storage target.
    """
    target = client_media_path(client)
    target.mkdir(parents=True, exist_ok=True)
    return target

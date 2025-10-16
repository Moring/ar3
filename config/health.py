"""
Application health reporting utilities.

The module keeps the request-facing views compact while offering a single
place to expand system checks as the platform grows. Each check function
returns a mapping suitable for JSON serialization, with the expectation that
future services (search, object storage, etc.) can plug in alongside the
existing database, Valkey, and queue checks.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
import subprocess
from typing import Any, Callable, Iterable

from django.conf import settings
from django.db import DatabaseError, connections

try:  # Optional dependency; commands should remain resilient if missing.
    import redis  # type: ignore
except ImportError:  # pragma: no cover - exercised when redis-py unavailable.
    redis = None


BOOT_TIME = datetime.now(timezone.utc)


@dataclass(frozen=True)
class CheckOutcome:
    """Normalized structure for individual health checks."""

    name: str
    status: str
    details: dict[str, Any]


def uptime_seconds() -> int:
    """Return the process uptime in whole seconds."""
    delta = datetime.now(timezone.utc) - BOOT_TIME
    return max(int(delta.total_seconds()), 0)


def get_git_version() -> str | None:
    """Best-effort Git identifier for the running code."""
    git_dir = settings.BASE_DIR
    commands: Iterable[list[str]] = (
        ["git", "-C", str(git_dir), "describe", "--tags", "--dirty", "--always"],
        ["git", "-C", str(git_dir), "rev-parse", "HEAD"],
    )
    for command in commands:
        try:
            output = subprocess.check_output(command, stderr=subprocess.DEVNULL)
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
        return output.decode().strip()
    return None


def run_checks() -> list[CheckOutcome]:
    """Execute the configured system checks."""
    checks: list[tuple[str, Callable[[], dict[str, Any]]]] = [
        ("db", check_database),
        ("valkey", check_valkey),
        ("queue", check_queue),
    ]

    outcomes: list[CheckOutcome] = []
    for name, checker in checks:
        try:
            details = checker()
        except CheckSkipped as skipped:
            outcomes.append(CheckOutcome(name=name, status="skipped", details={"reason": str(skipped)}))
        except Exception as exc:  # pragma: no cover - defensive catch for unexpected failures.
            outcomes.append(CheckOutcome(name=name, status="error", details={"error": str(exc)}))
        else:
            outcomes.append(CheckOutcome(name=name, status="ok", details=details))
    return outcomes


class CheckSkipped(RuntimeError):
    """Raised when a check cannot run due to missing configuration."""


def scrub_url(url: str) -> str:
    """Hide credentials in connection URLs while keeping host/port visible."""
    if "@" not in url:
        return url
    try:
        scheme, rest = url.split("://", 1)
    except ValueError:
        return url

    if "@" not in rest:
        return url

    _, host = rest.split("@", 1)
    return f"{scheme}://***:***@{host}"


def check_database() -> dict[str, Any]:
    """Ensure the default Django database is reachable."""
    connection = connections["default"]
    try:
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except DatabaseError as exc:
        raise Exception(f"database-unavailable: {exc}") from exc

    vendor = connection.vendor or "unknown"
    return {"vendor": vendor}


def _redis_client_from_url(url: str):
    if redis is None:
        raise Exception("redis-client-missing")
    return redis.Redis.from_url(url)


def check_valkey() -> dict[str, Any]:
    """Verify Valkey/Redis connectivity."""
    url = (
        getattr(settings, "VALKEY_URL", None)
        or getattr(settings, "REDIS_URL", None)
        or os.environ.get("VALKEY_URL")
        or os.environ.get("REDIS_URL")
    )

    if not url:
        raise CheckSkipped("no Valkey URL configured")

    client = _redis_client_from_url(url)
    client.ping()
    return {"url": scrub_url(url)}


def check_queue() -> dict[str, Any]:
    """Confirm the asynchronous worker backend is reachable."""
    huey_config = getattr(settings, "HUEY", None)
    if not huey_config:
        raise CheckSkipped("Huey queue not configured")

    # Support both dict-style configuration and instantiated Huey objects.
    immediate = getattr(huey_config, "immediate", None)
    if isinstance(huey_config, dict):
        immediate = huey_config.get("immediate") or huey_config.get("immediate_use_memory")

    if immediate:
        return {"mode": "immediate"}

    if isinstance(huey_config, dict):
        url = huey_config.get("connection", {}).get("url")
        if not url:
            raise CheckSkipped("Huey connection URL missing")
        client = _redis_client_from_url(url)
        client.ping()
        return {"backend": "redis", "url": scrub_url(url)}

    # For Huey objects we attempt to use their storage's connection.
    storage = getattr(huey_config, "storage", None)
    if storage is None:
        raise CheckSkipped("Huey storage backend unavailable")

    try:
        connection = storage.get_client()  # type: ignore[attr-defined]
    except AttributeError as exc:
        raise CheckSkipped(f"Huey storage client unsupported: {exc}") from exc

    # Redis-based storages expose a ping-capable client.
    if hasattr(connection, "ping"):
        connection.ping()
        return {"backend": storage.__class__.__name__}

    raise CheckSkipped(f"Unsupported Huey storage client type: {type(connection)!r}")

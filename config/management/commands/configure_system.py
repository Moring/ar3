"""
System configuration command that runs required setup tasks.

Additional steps can be registered in ``Command.steps`` and should be written
to be idempotent so that the command can be safely executed multiple times
at startup.
"""

from collections.abc import Iterable
from typing import Callable

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


DEFAULT_SUPERUSER_CONFIG = (
    {
        "username": "davmor",
        "password": "bV8vZF5CcbE8fBYPz7Tw",
        "email": "",
        "is_staff": True,
        "is_superuser": True,
    },
)


class Command(BaseCommand):
    help = "Configure the system by ensuring required accounts and other resources exist."

    def handle(self, *args, **options):
        for name, step in self.steps():
            self.stdout.write(f"Running step: {name}")
            step()

        self.stdout.write(self.style.SUCCESS("System configuration complete."))

    def steps(self) -> Iterable[tuple[str, Callable[[], None]]]:
        """Return ordered pairs of (name, callable) for configuration steps."""
        yield ("ensure-default-superusers", self.ensure_default_superusers)

    def ensure_default_superusers(self) -> None:
        """Create or update required superusers with the expected attributes."""
        self.ensure_superusers(DEFAULT_SUPERUSER_CONFIG)

    def ensure_superusers(self, entries: Iterable[dict]) -> None:
        """Create or update superusers using the provided configuration entries."""
        User = get_user_model()

        for entry in entries:
            username = entry["username"]
            password = entry.get("password")

            defaults = {
                key: value
                for key, value in entry.items()
                if key not in {"username", "password"}
            }
            defaults.setdefault("is_staff", True)
            defaults.setdefault("is_superuser", True)

            user, created = User.objects.update_or_create(
                username=username, defaults=defaults
            )

            if password:
                user.set_password(password)
                user.save(update_fields=["password"])

            action = "created" if created else "updated"
            self.stdout.write(f"{action} superuser '{username}'")

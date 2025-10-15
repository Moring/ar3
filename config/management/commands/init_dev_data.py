"""
Development data initialization helpers.

The command is intentionally data-driven so that additional seed objects can be
added by extending INIT_CONFIG without modifying the implementation.
"""

from collections.abc import Iterable

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


INIT_CONFIG = {
    "superusers": (
        {
            "username": "davmor",
            "password": "password",
            "email": "",
            "is_staff": True,
            "is_superuser": True,
        },
    ),
}


class Command(BaseCommand):
    help = "Idempotently seed development data such as superusers."

    def handle(self, *args, **options):
        self.ensure_superusers(INIT_CONFIG.get("superusers", ()))
        self.stdout.write(self.style.SUCCESS("Development objects initialized."))

    def ensure_superusers(self, users: Iterable[dict]) -> None:
        """Create or update superusers using the provided config."""
        User = get_user_model()
        for entry in users:
            username = entry["username"]
            password = entry.get("password")

            defaults = {key: value for key, value in entry.items() if key not in {"username", "password"}}
            defaults.setdefault("is_staff", True)
            defaults.setdefault("is_superuser", True)

            user, created = User.objects.update_or_create(username=username, defaults=defaults)

            if password:
                user.set_password(password)
                user.save(update_fields=["password"])

            action = "created" if created else "updated"
            self.stdout.write(f"{action} superuser '{username}'")

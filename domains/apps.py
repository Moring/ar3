from django.apps import AppConfig


class DomainsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "domains"

    def ready(self):
        super().ready()
        # Import signal handlers so client storage provisioning runs on create.
        from . import signals  # noqa: F401

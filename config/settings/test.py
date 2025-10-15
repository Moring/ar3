from .dev import *  # noqa: F401,F403

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
HUEY["immediate"] = True

# Use a lightweight local database for tests instead of the Docker Postgres
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "tmp" / "test.sqlite3",
    }
}

MEDIA_ROOT = BASE_DIR / "tmp" / "media"
STATIC_ROOT = BASE_DIR / "tmp" / "static"

# Disable pgvector integrations when the extension is unavailable locally
PGVECTOR_DISABLED = True

MIGRATION_MODULES = {
    "billing": None,
    "contexts": None,
    "domains": None,
    "prompts": None,
    "rbac": None,
    "uploads": None,
}

INSTALLED_APPS = [*INSTALLED_APPS, "config"]

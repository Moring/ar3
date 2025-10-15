from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from pathlib import Path
from .storage import client_media_path, ensure_client_media_path

User = get_user_model()

class Client(models.Model):
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    owner = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def domain_path(self):
        return client_media_path(self)

    def provision_storage(self):
        """Ensure the client's storage domain exists on disk."""
        return ensure_client_media_path(self)

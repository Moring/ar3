from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Client
from .storage import ensure_client_media_path


@receiver(post_save, sender=Client)
def create_client_media_bucket(sender, instance: Client, created: bool, **kwargs):
    if created and instance.slug:
        ensure_client_media_path(instance)

from django.db.models.signals import post_save
from django.dispatch import receiver

from domains.models import Client
from .models import Wallet


@receiver(post_save, sender=Client)
def ensure_wallet_exists(sender, instance: Client, created: bool, **kwargs):
    if created:
        Wallet.objects.get_or_create(client=instance)

from pathlib import Path

from django.db import models
from django.core.exceptions import ValidationError
from taggit.managers import TaggableManager

from contexts.models import Category
from domains.models import Client

def upload_to(instance, filename):
    return f"{instance.client.slug}/{filename}"

class File(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to=upload_to)
    size = models.BigIntegerField(default=0)
    content_type = models.CharField(max_length=200, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    tags = TaggableManager(blank=True)

    class Meta:
        ordering = ["-uploaded_at"]

    def clean(self):
        if not self.category_id:
            raise ValidationError("Category is required for uploaded files.")

    def save(self, *args, **kwargs):
        self.clean()
        if hasattr(self.file, "size"):
            self.size = self.file.size
        if hasattr(self.file, "content_type") and self.file.content_type:
            self.content_type = self.file.content_type
        self.client.provision_storage()
        super().save(*args, **kwargs)

    @property
    def filename(self) -> str:
        return Path(self.file.name).name

    def __str__(self):
        return f"{self.client.slug}:{self.filename}"

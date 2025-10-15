from django.conf import settings
from django.db import models
from django.utils.text import slugify
from pgvector.django import VectorField


class ListVectorField(VectorField):
    """VectorField that always returns a plain Python list when possible."""

    def _coerce(self, value):
        if value is None:
            return None
        if isinstance(value, list):
            return value
        if hasattr(value, "tolist"):
            return value.tolist()
        if isinstance(value, tuple):
            return list(value)
        try:
            return list(value)
        except TypeError:
            return value

    def to_python(self, value):
        coerced = super().to_python(value)
        return self._coerce(coerced)

    def from_db_value(self, value, expression, connection):
        coerced = super().from_db_value(value, expression, connection)
        return self._coerce(coerced)

    def get_prep_value(self, value):
        if getattr(settings, "PGVECTOR_DISABLED", False):
            # When pgvector is disabled we persist embeddings as JSON-compatible lists.
            return self._coerce(value)
        return super().get_prep_value(value)


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=150, unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class DocumentChunk(models.Model):
    file = models.ForeignKey("uploads.File", on_delete=models.CASCADE, related_name="chunks")
    text = models.TextField()
    embedding = ListVectorField(dimensions=1536, null=True, blank=True)
    score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["file"]),
        ]

    def __str__(self):
        return f"Chunk {self.pk} for {self.file}"

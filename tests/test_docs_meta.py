import pytest
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

from domains.models import Client
from contexts.models import Category
from uploads.models import File

@pytest.mark.story("S-014")
def test_upload_requires_category(settings, tmp_path, django_user_model):
    settings.MEDIA_ROOT = tmp_path
    user = django_user_model.objects.create_user(username="u2", password="p")
    c = Client.objects.create(name="Beta", owner=user)
    with pytest.raises(ValidationError):
        File.objects.create(client=c, file=ContentFile(b'x', name="x.txt"), size=1, content_type="text/plain")  # missing category

@pytest.mark.story("S-014")
def test_add_and_filter_by_tags(settings, tmp_path, django_user_model):
    settings.MEDIA_ROOT = tmp_path
    user = django_user_model.objects.create_user(username="u3", password="p")
    c = Client.objects.create(name="Gamma", owner=user)
    cat = Category.objects.create(name="General", slug="general")
    f = File.objects.create(client=c, file=ContentFile(b'x', name="x.txt"), size=1, content_type="text/plain", category=cat)
    f.tags.add("alpha", "beta")
    assert set(list(f.tags.names())) == {"alpha","beta"}

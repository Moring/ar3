import pytest
from django.core.files.base import ContentFile

from contexts.models import Category
from domains.models import Client
from uploads.models import File
from uploads.query import select_docs


@pytest.mark.story("S-015")
def test_select_docs_no_duplicates(settings, tmp_path, django_user_model):
    settings.MEDIA_ROOT = tmp_path
    client = Client.objects.create(name="Acme")
    cat_a = Category.objects.create(name="General")
    cat_b = Category.objects.create(name="Finance")

    f1 = File.objects.create(client=client, file=ContentFile(b"a", name="a.txt"), category=cat_a)
    f1.tags.add("alpha")
    f2 = File.objects.create(client=client, file=ContentFile(b"b", name="b.txt"), category=cat_b)
    f2.tags.add("alpha")

    results = select_docs(categories=[cat_a], tags=["alpha"])
    assert set(results) == {f1, f2}

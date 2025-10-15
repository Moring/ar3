import pytest

from contexts.models import Category


@pytest.mark.story("S-009")
def test_create_category(db):
    cat = Category.objects.create(name="General")
    assert cat.slug == "general"

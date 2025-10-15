import pytest
from domains.models import Client

@pytest.mark.story("S-012")
def test_domain_path_created(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    c = Client.objects.create(name="Acme")
    path = c.domain_path
    assert path.as_posix().endswith("/acme")
    assert path.exists()

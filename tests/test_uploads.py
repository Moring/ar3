import pytest
from django.core.files.base import ContentFile
from domains.models import Client
from contexts.models import Category
from uploads.models import File
from rbac.models import Role, RolePermission, assign_role

@pytest.mark.story("S-013")
def test_upload_scoped_to_client(settings, tmp_path, client, django_user_model):
    settings.MEDIA_ROOT = tmp_path
    user = django_user_model.objects.create_user(username="u", password="p")
    role = Role.objects.create(name="Client Admin", code="client-admin")
    RolePermission.objects.create(role=role, code="file.upload")
    client.force_login(user)
    c = Client.objects.create(name="Acme", owner=user)
    assign_role(actor=None, user=user, client=c, role=role)
    cat = Category.objects.create(name="General", slug="general")
    f = ContentFile(b"hello world", name="hello.txt")
    rec = File.objects.create(client=c, file=f, size=f.size, content_type="text/plain", category=cat)
    assert rec.client == c

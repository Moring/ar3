import pytest

from domains.models import Client
from rbac import models as rbac_models


@pytest.fixture
def client_and_role(db, django_user_model):
    client = Client.objects.create(name="Acme")
    role = rbac_models.Role.objects.create(name="Client Admin", code="client-admin")
    rbac_models.RolePermission.objects.create(role=role, code="client.update")
    user = django_user_model.objects.create_user(username="carol", password="pw")
    return client, role, user


@pytest.mark.story("S-010")
def test_client_admin_can_edit_client(client_and_role, django_user_model):
    client, role, user = client_and_role
    rbac_models.assign_role(actor=None, user=user, client=client, role=role)
    assert rbac_models.user_has_permission(user, client, "client.update")


@pytest.mark.story("S-010")
def test_non_admin_cannot_edit_client(client_and_role, django_user_model):
    client, role, user = client_and_role
    other_client = Client.objects.create(name="Beta")
    assert not rbac_models.user_has_permission(user, client, "client.update")
    assert not rbac_models.user_has_permission(user, other_client, "client.update")

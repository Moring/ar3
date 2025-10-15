import pytest

from django.contrib.auth import get_user_model

from domains.models import Client
from rbac import models as rbac_models


User = get_user_model()


@pytest.fixture
def role_hierarchy(db):
    org_admin = rbac_models.Role.objects.create(name="Org Admin", code="org-admin")
    client_admin = rbac_models.Role.objects.create(name="Client Admin", code="client-admin", parent=org_admin)
    user_role = rbac_models.Role.objects.create(name="User", code="user", parent=client_admin)
    rbac_models.RolePermission.objects.create(role=org_admin, code="client.view")
    rbac_models.RolePermission.objects.create(role=client_admin, code="client.edit")
    return org_admin, client_admin, user_role


@pytest.mark.story("S-006")
def test_role_hierarchy_inherits_perms(role_hierarchy, django_user_model):
    _, client_admin, user_role = role_hierarchy
    user = django_user_model.objects.create_user(username="alice", password="pw")
    client = Client.objects.create(name="Acme")
    rbac_models.assign_role(actor=None, user=user, client=client, role=client_admin)

    assert rbac_models.user_has_permission(user, client, "client.view")
    assert rbac_models.user_has_permission(user, client, "client.edit")


@pytest.mark.story("S-006")
def test_client_scoped_access(role_hierarchy, django_user_model):
    _, client_admin, _ = role_hierarchy
    user = django_user_model.objects.create_user(username="bob", password="pw")
    client_one = Client.objects.create(name="Acme")
    client_two = Client.objects.create(name="Beta")
    rbac_models.assign_role(actor=None, user=user, client=client_one, role=client_admin)

    assert rbac_models.user_has_permission(user, client_one, "client.edit")
    assert not rbac_models.user_has_permission(user, client_two, "client.edit")

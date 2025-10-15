import pytest

from django.contrib.auth import get_user_model

from domains.models import Client
from rbac import models as rbac_models


User = get_user_model()


@pytest.fixture
def admin_setup(db, django_user_model):
    actor = django_user_model.objects.create_user(username="admin", password="pw")
    target = django_user_model.objects.create_user(username="user", password="pw")
    client = Client.objects.create(name="Acme")
    role = rbac_models.Role.objects.create(name="Client Admin", code="client-admin")
    return actor, target, client, role


@pytest.mark.story("S-008")
def test_assign_role_flow(admin_setup):
    actor, target, client, role = admin_setup
    assignment = rbac_models.assign_role(actor=actor, user=target, client=client, role=role)
    assert assignment.role == role
    audit = rbac_models.RoleAssignmentAudit.objects.first()
    assert audit.action == "assign"
    assert audit.user == actor


@pytest.mark.story("S-008")
def test_remove_role_flow(admin_setup):
    actor, target, client, role = admin_setup
    rbac_models.assign_role(actor=actor, user=target, client=client, role=role)
    rbac_models.remove_role(actor=actor, user=target, client=client)
    assert not rbac_models.ClientRoleAssignment.objects.filter(user=target, client=client).exists()
    audit = rbac_models.RoleAssignmentAudit.objects.filter(action="remove").first()
    assert audit is not None


@pytest.mark.story("S-008")
def test_audit_trail_written(admin_setup):
    actor, target, client, role = admin_setup
    rbac_models.assign_role(actor=actor, user=target, client=client, role=role, notes="initial grant")
    rbac_models.remove_role(actor=actor, user=target, client=client, notes="cleanup")
    assign_note = rbac_models.RoleAssignmentAudit.objects.filter(action="assign").first().notes
    remove_note = rbac_models.RoleAssignmentAudit.objects.filter(action="remove").first().notes
    assert "initial grant" in assign_note
    assert "cleanup" in remove_note

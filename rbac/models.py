from __future__ import annotations

from typing import Iterable, Optional, Set

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
from mptt.models import MPTTModel, TreeForeignKey

from domains.models import Client

User = get_user_model()


class Role(MPTTModel):
    name = models.CharField(max_length=100, unique=True)
    code = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    parent = TreeForeignKey("self", null=True, blank=True, related_name="children", on_delete=models.CASCADE)

    class MPTTMeta:
        order_insertion_by = ["name"]

    def __str__(self):
        return self.name

    def permission_codes(self) -> Set[str]:
        codes: Set[str] = set()
        for node in self.get_ancestors(include_self=True):
            codes.update(node.permissions.values_list("code", flat=True))
        return codes


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="permissions")
    code = models.CharField(max_length=120)

    class Meta:
        unique_together = ("role", "code")

    def __str__(self):
        return f"{self.role.code}:{self.code}"


class ClientRoleAssignment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="client_roles")
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="role_assignments")
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="assignments")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "client")

    def __str__(self):
        return f"{self.user} -> {self.role} ({self.client})"

    def inherited_permissions(self) -> Set[str]:
        return self.role.permission_codes()


class RoleAssignmentAudit(models.Model):
    ACTION_CHOICES = [
        ("assign", "Assign"),
        ("remove", "Remove"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="role_assignment_events")
    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="role_assignment_targets")
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]


def assign_role(*, actor: Optional[User], user: User, client: Client, role: Role, notes: str = "") -> ClientRoleAssignment:
    with transaction.atomic():
        assignment, created = ClientRoleAssignment.objects.update_or_create(
            user=user,
            client=client,
            defaults={"role": role},
        )
        RoleAssignmentAudit.objects.create(user=actor, target_user=user, client=client, role=role, action="assign", notes=notes)
    return assignment


def remove_role(*, actor: Optional[User], user: User, client: Client, notes: str = "") -> None:
    with transaction.atomic():
        try:
            assignment = ClientRoleAssignment.objects.get(user=user, client=client)
        except ClientRoleAssignment.DoesNotExist:
            raise ValidationError("Role assignment does not exist.")
        RoleAssignmentAudit.objects.create(user=actor, target_user=user, client=client, role=assignment.role, action="remove", notes=notes)
        assignment.delete()


def user_has_permission(user: User, client: Client, permission: str) -> bool:
    try:
        assignment = ClientRoleAssignment.objects.get(user=user, client=client)
    except ClientRoleAssignment.DoesNotExist:
        return False
    perms = assignment.inherited_permissions()
    return permission in perms


def user_roles_for_client(user: User, client: Client) -> Iterable[Role]:
    return Role.objects.filter(assignments__user=user, assignments__client=client)


def primary_client_for_user(user: User) -> Optional[Client]:
    assignment = ClientRoleAssignment.objects.select_related("client").filter(user=user).order_by("client__name").first()
    return assignment.client if assignment else None

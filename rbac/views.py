from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect, render

from .forms import RoleAssignmentForm, RoleRemovalForm
from .models import ClientRoleAssignment, Role


def staff_required(view_func):
    return user_passes_test(lambda u: u.is_staff, login_url="/accounts/login/")(view_func)


@staff_required
def admin_dashboard(request):
    assignment_form = RoleAssignmentForm(request.POST or None)
    removal_form = RoleRemovalForm(request.POST or None)

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "assign" and assignment_form.is_valid():
            assignment_form.save(actor=request.user)
            messages.success(request, "Role assignment saved.")
            return redirect("rbac_admin")
        elif action == "remove" and removal_form.is_valid():
            removal_form.save(actor=request.user)
            messages.success(request, "Role assignment removed.")
            return redirect("rbac_admin")
        else:
            messages.error(request, "Unable to process the request. Please review the form.")

    assignments = list(ClientRoleAssignment.objects.select_related("user", "client", "role").order_by("client__name", "user__username"))
    for assignment in assignments:
        assignment.permission_list = sorted(assignment.inherited_permissions())
    roles = Role.objects.all().order_by("name")
    return render(
        request,
        "rbac/admin.html",
        {
            "assignment_form": assignment_form,
            "removal_form": removal_form,
            "assignments": assignments,
            "roles": roles,
        },
    )

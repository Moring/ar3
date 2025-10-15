from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from rbac.models import ClientRoleAssignment, user_has_permission

from .forms import ClientForm
from .models import Client


def _get_user_assignment(user, client_id=None):
    qs = ClientRoleAssignment.objects.select_related("client", "role").filter(user=user)
    if client_id:
        qs = qs.filter(client__id=client_id)
    return qs.first()


@login_required
def client_profile(request, client_id=None):
    assignment = _get_user_assignment(request.user, client_id)
    client = assignment.client if assignment else None

    if client is None and request.user.is_staff:
        if client_id:
            client = get_object_or_404(Client, pk=client_id)
        else:
            client = Client.objects.order_by("name").first()

    if client is None:
        messages.error(request, "You do not have access to that client.")
        return redirect("index")

    if not request.user.is_staff and not user_has_permission(request.user, client, "client.update"):
        messages.error(request, "You do not have permission to edit this client.")
        return redirect("index")

    form = ClientForm(request.POST or None, instance=client)
    if request.method == "POST" and form.is_valid():
        form.save()
        client.provision_storage()
        messages.success(request, "Client profile updated.")
        return redirect("client_profile", client_id=client.id)

    context = {
        "form": form,
        "client": client,
        "assignments": ClientRoleAssignment.objects.filter(user=request.user).select_related("client", "role"),
    }
    if request.user.is_staff:
        context["clients"] = Client.objects.order_by("name")
    return render(request, "domains/client_profile.html", context)

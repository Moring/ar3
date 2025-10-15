from django import forms
from django.contrib.auth import get_user_model

from domains.models import Client
from .models import Role, ClientRoleAssignment


User = get_user_model()


class RoleAssignmentForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.all(), label="User")
    client = forms.ModelChoiceField(queryset=Client.objects.all(), label="Client")
    role = forms.ModelChoiceField(queryset=Role.objects.all(), label="Role")
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        selects = ["user", "client", "role"]
        for name in selects:
            self.fields[name].widget.attrs.update({"class": "form-select"})
        self.fields["notes"].widget.attrs.update({"class": "form-control", "placeholder": "Optional context"})

    def save(self, *, actor):
        from .models import assign_role

        return assign_role(
            actor=actor,
            user=self.cleaned_data["user"],
            client=self.cleaned_data["client"],
            role=self.cleaned_data["role"],
            notes=self.cleaned_data.get("notes", ""),
        )


class RoleRemovalForm(forms.Form):
    assignment = forms.ModelChoiceField(queryset=ClientRoleAssignment.objects.select_related("user", "client", "role"), label="Assignment")
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["assignment"].widget.attrs.update({"class": "form-select"})
        self.fields["notes"].widget.attrs.update({"class": "form-control", "placeholder": "Reason for removal"})

    def save(self, *, actor):
        from .models import remove_role

        assignment = self.cleaned_data["assignment"]
        remove_role(actor=actor, user=assignment.user, client=assignment.client, notes=self.cleaned_data.get("notes", ""))

from django import forms

from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["name", "slug"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Acme Corporation"}),
            "slug": forms.TextInput(attrs={"class": "form-control", "placeholder": "acme"}),
        }

    def clean_slug(self):
        slug = self.cleaned_data["slug"]
        if not slug:
            slug = self.cleaned_data["name"]
        return slug

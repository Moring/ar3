from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect, render

from .forms import CategoryForm
from .models import Category


def staff_required(view_func):
    return user_passes_test(lambda u: u.is_staff, login_url="/accounts/login/")(view_func)


@staff_required
def category_admin(request):
    form = CategoryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        category = form.save()
        messages.success(request, f"Category '{category.name}' created.")
        return redirect("category_admin")

    categories = Category.objects.all().order_by("name")
    return render(
        request,
        "contexts/categories.html",
        {
            "form": form,
            "categories": categories,
        },
    )

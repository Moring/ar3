from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect, render

from contexts.models import Category
from rbac.models import primary_client_for_user, user_has_permission
from .models import File


@login_required
def file_manager(request):
    client = primary_client_for_user(request.user)
    if not client:
        return HttpResponseForbidden()
    files = list(File.objects.filter(client=client).prefetch_related("tags", "category"))
    for document in files:
        document.tag_list = list(document.tags.names())
    return render(request, "uploads/file_manager.html", {"files": files})


@login_required
def upload(request):
    client = primary_client_for_user(request.user)
    if not client:
        return HttpResponseForbidden()
    if not user_has_permission(request.user, client, "file.upload"):
        return HttpResponseForbidden()

    categories = Category.objects.all().order_by("name")

    if request.method == "POST":
        uploaded = request.FILES.get("file")
        category_id = request.POST.get("category")
        if uploaded and category_id:
            category = Category.objects.get(pk=category_id)
            record = File.objects.create(
                client=client,
                file=uploaded,
                size=getattr(uploaded, "size", 0),
                content_type=getattr(uploaded, "content_type", ""),
                category=category,
            )
            tags = [tag.strip() for tag in request.POST.get("tags", "").split(",") if tag.strip()]
            if tags:
                record.tags.add(*tags)
            messages.success(request, "File uploaded successfully.")
            return redirect("file_manager")
        messages.error(request, "Please choose both a file and category.")

    return render(request, "uploads/upload.html", {"categories": categories})

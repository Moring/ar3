from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render

def healthz(request):
    return JsonResponse({"ok": True})

def index(request):
    return render(request, "ui/index.html")

@user_passes_test(lambda u: u.is_staff, login_url="/accounts/login/")
def admin_portal(request):
    return render(request, "ui/admin_portal.html")

def partial_example(request):
    if request.headers.get("HX-Request") == "true" or request.headers.get("Hx-Request") == "true":
        return HttpResponse("<div>HTMX fragment ok</div>")
    return HttpResponse(status=400)

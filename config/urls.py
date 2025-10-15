from django.contrib import admin
from django.urls import path, include
from ui.views import healthz

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", healthz, name="healthz"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("rbac/", include("rbac.urls")),
    path("contexts/", include("contexts.urls")),
    path("clients/", include("domains.urls")),
    path("", include("ui.urls")),
    path("uploads/", include("uploads.urls")),
]

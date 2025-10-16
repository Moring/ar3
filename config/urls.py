from django.contrib import admin
from django.urls import include, path

from ui.views import health, healthz

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz", healthz, name="healthz"),
    path("health", health, name="health"),
    path("accounts/", include("django.contrib.auth.urls")),
    path("rbac/", include("rbac.urls")),
    path("contexts/", include("contexts.urls")),
    path("clients/", include("domains.urls")),
    path("", include("ui.urls")),
    path("uploads/", include("uploads.urls")),
]

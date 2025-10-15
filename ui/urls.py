from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("admin-portal/", views.admin_portal, name="admin_portal"),
    path("partial-example/", views.partial_example, name="partial_example"),
]

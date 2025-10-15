from django.urls import path

from . import views

urlpatterns = [
    path("categories/", views.category_admin, name="category_admin"),
]

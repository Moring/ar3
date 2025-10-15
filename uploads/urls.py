from django.urls import path
from . import views
urlpatterns = [
    path("manager/", views.file_manager, name="file_manager"),
    path("upload/", views.upload, name="upload"),
]

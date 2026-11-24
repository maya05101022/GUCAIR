from django.urls import path

from . import views

app_name = "resources"

urlpatterns = [
    path("", views.resource_list, name="list"),
    path("manage/", views.manage_resources, name="manage"),
    path("manage/new/", views.resource_create, name="create"),
    path("manage/<slug:slug>/edit/", views.resource_edit, name="edit"),
    path("manage/<slug:slug>/delete/", views.resource_delete, name="delete"),
    path("<slug:slug>/", views.resource_detail, name="detail"),
]

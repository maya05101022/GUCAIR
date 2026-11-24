from django.urls import path

from . import views

app_name = "universities"

urlpatterns = [
    path("", views.university_list, name="list"),
    path("register/", views.university_create, name="create"),
    path("edit/", views.university_edit, name="edit"),
    path("manage/", views.manage_universities, name="manage"),
    path("manage/<int:pk>/edit/", views.admin_edit_university, name="admin_edit"),
    path("manage/<int:pk>/approve/", views.approve_university, name="approve"),
    path("manage/<int:pk>/reject/", views.reject_university, name="reject"),
    path("manage/<int:pk>/delete/", views.delete_university, name="delete"),
    path("<slug:slug>/", views.university_detail, name="detail"),
]

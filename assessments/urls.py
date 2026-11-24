from django.urls import path

from . import views

app_name = "assessments"

urlpatterns = [
    path("", views.assessment_overview, name="overview"),
    path("new/", views.take_assessment, name="take"),
    path("history/", views.assessment_history, name="history"),
    path("manage/", views.manage_assessments, name="manage"),
    path("<int:pk>/", views.assessment_detail, name="detail"),
    path("<int:pk>/delete/", views.delete_assessment, name="delete"),
]

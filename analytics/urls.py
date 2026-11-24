from django.urls import path

from . import views

app_name = "analytics"

urlpatterns = [
    path("", views.analytics_dashboard, name="dashboard"),
    path("compare/", views.comparison, name="comparison"),
    path("api/summary/", views.public_stats_api, name="summary_api"),
]

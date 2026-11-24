from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("health/", views.health, name="health"),
    path("manage/messages/", views.contact_messages, name="contact_messages"),
    path(
        "manage/messages/<int:pk>/toggle/",
        views.toggle_contact_message,
        name="toggle_contact_message",
    ),
]

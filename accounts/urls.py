from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.GUCAIRLoginView.as_view(), name="login"),
    path("logout/", views.GUCAIRLogoutView.as_view(), name="logout"),
    path("profile/", views.profile, name="profile"),
    path(
        "password/",
        views.GUCAIRPasswordChangeView.as_view(),
        name="password_change",
    ),
    path("manage/users/", views.user_list, name="user_list"),
    path(
        "manage/users/<int:pk>/toggle-active/",
        views.user_toggle_active,
        name="user_toggle_active",
    ),
    path(
        "manage/users/<int:pk>/set-role/",
        views.user_set_role,
        name="user_set_role",
    ),
]

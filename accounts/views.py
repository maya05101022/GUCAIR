from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from .decorators import admin_required
from .forms import (
    GUCAIRLoginForm,
    RepresentativeProfileForm,
    RepresentativeRegistrationForm,
    StyledPasswordChangeForm,
)
from .models import UserProfile


def register(request):
    if request.user.is_authenticated:
        messages.info(request, "You are already signed in.")
        return redirect("dashboard:home")

    if request.method == "POST":
        form = RepresentativeRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(
                request,
                "Your representative account and university profile were created. "
                "An administrator must approve the university before assessments unlock.",
            )
            return redirect("dashboard:home")
        messages.error(request, "Please review the highlighted fields and try again.")
    else:
        form = RepresentativeRegistrationForm()

    return render(request, "accounts/register.html", {"form": form})


class GUCAIRLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = GUCAIRLoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, f"Welcome back, {self.request.user.get_short_name() or self.request.user.username}."
        )
        return response

    def form_invalid(self, form):
        messages.error(self.request, "Sign-in failed. Check your username and password.")
        return super().form_invalid(form)


class GUCAIRLogoutView(LogoutView):
    next_page = reverse_lazy("core:landing")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "You have been signed out.")
        return super().dispatch(request, *args, **kwargs)


@login_required
def profile(request):
    profile_obj, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        form = RepresentativeProfileForm(request.POST, instance=profile_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated.")
            return redirect("accounts:profile")
        messages.error(request, "Please correct the highlighted fields.")
    else:
        form = RepresentativeProfileForm(instance=profile_obj)

    context = {
        "form": form,
        "profile_obj": profile_obj,
        "university": profile_obj.university,
    }
    return render(request, "accounts/profile.html", context)


class GUCAIRPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = "accounts/password_change.html"
    form_class = StyledPasswordChangeForm
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form):
        messages.success(self.request, "Your password has been changed.")
        return super().form_valid(form)


@admin_required
def user_list(request):
    q = request.GET.get("q", "").strip()
    role = request.GET.get("role", "")
    status = request.GET.get("status", "")

    users = User.objects.select_related("profile", "profile__university").order_by(
        "username"
    )
    if q:
        users = users.filter(
            Q(username__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(email__icontains=q)
        )
    if role == "admin":
        users = users.filter(Q(profile__role="admin") | Q(is_superuser=True) | Q(is_staff=True))
    elif role == "representative":
        users = users.filter(profile__role="representative")
    if status == "active":
        users = users.filter(is_active=True)
    elif status == "inactive":
        users = users.filter(is_active=False)

    paginator = Paginator(users, 10)
    page = paginator.get_page(request.GET.get("page"))
    querystring = request.GET.copy()
    querystring.pop("page", None)

    return render(
        request,
        "accounts/user_list.html",
        {
            "page_obj": page,
            "users": page.object_list,
            "q": q,
            "role": role,
            "status": status,
            "querystring": querystring.urlencode(),
            "total_users": users.count(),
        },
    )


@require_POST
@admin_required
def user_toggle_active(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, "You cannot deactivate your own account.")
        return redirect("accounts:user_list")
    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])
    messages.success(
        request,
        f"{user.username} is now {'active' if user.is_active else 'inactive'}.",
    )
    return redirect(request.POST.get("next") or "accounts:user_list")


@require_POST
@admin_required
def user_set_role(request, pk):
    user = get_object_or_404(User, pk=pk)
    role = request.POST.get("role")
    if role not in dict(UserProfile.ROLE_CHOICES):
        messages.error(request, "Unknown role requested.")
        return redirect("accounts:user_list")
    profile_obj, _ = UserProfile.objects.get_or_create(user=user)
    if user == request.user and role != UserProfile.ROLE_ADMIN:
        messages.error(request, "You cannot remove your own administrator role.")
        return redirect("accounts:user_list")
    profile_obj.role = role
    profile_obj.save(update_fields=["role"])
    user.is_staff = role == UserProfile.ROLE_ADMIN
    user.save(update_fields=["is_staff"])
    messages.success(request, f"{user.username} now has the {profile_obj.get_role_display()} role.")
    return redirect(request.POST.get("next") or "accounts:user_list")

from functools import wraps

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect


def is_administrator(user) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    profile = getattr(user, "profile", None)
    return bool(profile and profile.role == "admin")


def is_representative(user) -> bool:
    return user.is_authenticated and not is_administrator(user)


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/accounts/login/?next={request.path}")
        if not is_administrator(request.user):
            raise PermissionDenied("Administrator access is required.")
        return view_func(request, *args, **kwargs)

    return _wrapped


def representative_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/accounts/login/?next={request.path}")
        if not is_representative(request.user):
            messages.info(request, "This area is for university representatives.")
            return redirect("dashboard:admin_home")
        if not getattr(request.user.profile, "university_id", None):
            messages.warning(
                request,
                "Register your university profile before using this feature.",
            )
            return redirect("universities:create")
        return view_func(request, *args, **kwargs)

    return _wrapped


def representative_or_admin_required(view_func):
    """Allow administrators and representatives with a linked university."""

    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/accounts/login/?next={request.path}")
        if is_administrator(request.user):
            return view_func(request, *args, **kwargs)
        if not getattr(request.user.profile, "university_id", None):
            messages.warning(
                request,
                "Register your university profile before using this feature.",
            )
            return redirect("universities:create")
        return view_func(request, *args, **kwargs)

    return _wrapped


def approved_university_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"/accounts/login/?next={request.path}")
        if not is_representative(request.user):
            messages.info(request, "This area is for university representatives.")
            return redirect("dashboard:admin_home")
        university = getattr(request.user.profile, "university", None)
        if not university:
            messages.warning(
                request, "Register your university profile before continuing."
            )
            return redirect("universities:create")
        if not university.is_approved:
            messages.warning(
                request,
                "Your university registration is awaiting approval. "
                "Assessments unlock once an administrator approves your institution.",
            )
            return redirect("dashboard:home")
        return view_func(request, *args, **kwargs)

    return _wrapped

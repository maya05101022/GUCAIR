from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import admin_required, is_administrator

from .forms import UniversityAdminForm, UniversityForm
from .models import COUNTRIES, University


def _visible_university(request, slug):
    university = get_object_or_404(University, slug=slug)
    if not university.is_approved:
        is_owner = (
            request.user.is_authenticated
            and request.user.profile.university_id == university.pk
        )
        if not (is_owner or is_administrator(request.user)):
            raise Http404("University not found")
    return university


def university_list(request):
    q = request.GET.get("q", "").strip()
    country = request.GET.get("country", "").strip()
    universities = (
        University.objects.approved()
        .annotate(assessment_count=Count("assessments", distinct=True))
        .order_by("name")
    )
    if q:
        universities = universities.filter(
            Q(name__icontains=q) | Q(city__icontains=q) | Q(description__icontains=q)
        )
    if country:
        universities = universities.filter(country=country)

    paginator = Paginator(universities, 9)
    page = paginator.get_page(request.GET.get("page"))
    querystring = request.GET.copy()
    querystring.pop("page", None)

    return render(
        request,
        "universities/list.html",
        {
            "page_obj": page,
            "universities": page.object_list,
            "q": q,
            "country": country,
            "countries": COUNTRIES,
            "querystring": querystring.urlencode(),
            "total_results": universities.count(),
        },
    )


def university_detail(request, slug):
    university = _visible_university(request, slug)
    latest = university.assessments.select_related().order_by("-created_at").first()
    results = latest.ordered_results if latest else []
    history = university.assessments.order_by("-created_at")[:6] if request.user.is_authenticated else []
    can_view_scores = request.user.is_authenticated
    return render(
        request,
        "universities/detail.html",
        {
            "university": university,
            "latest": latest,
            "results": results,
            "history": history,
            "can_view_scores": can_view_scores,
            "is_owner": request.user.is_authenticated
            and request.user.profile.university_id == university.pk,
        },
    )


@login_required
def university_create(request):
    if not request.user.is_authenticated:
        return redirect("accounts:login")
    if is_administrator(request.user):
        messages.info(
            request,
            "Administrators add institutions through the university management area.",
        )
        return redirect("universities:manage")
    profile = request.user.profile
    if profile.university_id:
        messages.info(request, "Your account is already linked to a university.")
        return redirect("universities:edit")

    if request.method == "POST":
        form = UniversityForm(request.POST)
        if form.is_valid():
            university = form.save(commit=False)
            university.created_by = request.user
            university.status = University.STATUS_PENDING
            university.save()
            profile.university = university
            profile.save(update_fields=["university"])
            messages.success(
                request,
                "University profile submitted for review. Assessments unlock after approval.",
            )
            return redirect("dashboard:home")
        messages.error(request, "Please correct the highlighted fields.")
    else:
        form = UniversityForm()

    return render(request, "universities/form.html", {"form": form, "is_create": True})


@login_required
def university_edit(request):
    profile = request.user.profile
    if is_administrator(request.user):
        messages.info(
            request, "Use university management to edit institutional records."
        )
        return redirect("universities:manage")
    university = profile.university
    if not university:
        return redirect("universities:create")

    if request.method == "POST":
        form = UniversityForm(request.POST, instance=university)
        if form.is_valid():
            form.save()
            messages.success(request, "University profile updated.")
            return redirect("dashboard:home")
        messages.error(request, "Please correct the highlighted fields.")
    else:
        form = UniversityForm(instance=university)

    return render(
        request,
        "universities/form.html",
        {"form": form, "university": university, "is_create": False},
    )


@admin_required
def admin_edit_university(request, pk):
    university = get_object_or_404(University, pk=pk)
    if request.method == "POST":
        form = UniversityAdminForm(request.POST, instance=university)
        if form.is_valid():
            updated = form.save(commit=False)
            if updated.status == University.STATUS_APPROVED and not updated.approved_at:
                updated.approved_at = timezone.now()
            if updated.status != University.STATUS_APPROVED:
                updated.approved_at = None
            updated.save()
            messages.success(request, f"{university.name} updated.")
            return redirect("universities:manage")
        messages.error(request, "Please correct the highlighted fields.")
    else:
        form = UniversityAdminForm(instance=university)

    return render(
        request,
        "universities/admin_form.html",
        {"form": form, "university": university},
    )


@admin_required
def manage_universities(request):
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    country = request.GET.get("country", "")

    universities = (
        University.objects.select_related("created_by")
        .annotate(assessment_count=Count("assessments", distinct=True))
        .order_by("-created_at")
    )
    if q:
        universities = universities.filter(
            Q(name__icontains=q) | Q(city__icontains=q) | Q(created_by__username__icontains=q)
        )
    if status in dict(University.STATUS_CHOICES):
        universities = universities.filter(status=status)
    if country:
        universities = universities.filter(country=country)

    paginator = Paginator(universities, 10)
    page = paginator.get_page(request.GET.get("page"))
    querystring = request.GET.copy()
    querystring.pop("page", None)

    return render(
        request,
        "universities/manage.html",
        {
            "page_obj": page,
            "universities": page.object_list,
            "q": q,
            "status": status,
            "country": country,
            "status_choices": University.STATUS_CHOICES,
            "countries": COUNTRIES,
            "querystring": querystring.urlencode(),
            "pending_count": University.objects.pending().count(),
        },
    )


@require_POST
@admin_required
def approve_university(request, pk):
    university = get_object_or_404(University, pk=pk)
    university.status = University.STATUS_APPROVED
    university.approved_at = timezone.now()
    university.review_note = request.POST.get("review_note", "").strip()
    university.save(update_fields=["status", "approved_at", "review_note", "updated_at"])
    messages.success(request, f"{university.name} has been approved.")
    return redirect(request.POST.get("next") or "universities:manage")


@require_POST
@admin_required
def reject_university(request, pk):
    university = get_object_or_404(University, pk=pk)
    note = request.POST.get("review_note", "").strip()
    university.status = University.STATUS_REJECTED
    university.approved_at = None
    university.review_note = note or "Registration did not meet consortium requirements."
    university.save(update_fields=["status", "approved_at", "review_note", "updated_at"])
    messages.warning(request, f"{university.name} registration was rejected.")
    return redirect(request.POST.get("next") or "universities:manage")


@require_POST
@admin_required
def delete_university(request, pk):
    university = get_object_or_404(University, pk=pk)
    if request.POST.get("confirm_name", "").strip() != university.name:
        messages.error(
            request,
            "Deletion cancelled: type the exact university name to confirm.",
        )
        return redirect(request.POST.get("next") or "universities:manage")
    name = university.name
    university.delete()
    messages.success(request, f"{name} and its related assessment records were deleted.")
    return redirect("universities:manage")

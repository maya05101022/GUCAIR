from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Max
from django.shortcuts import redirect, render
from django.utils import timezone

from accounts.decorators import admin_required, is_administrator
from assessments.models import Assessment
from assessments.services import build_recommendations
from core.models import ContactMessage
from resources.models import Resource
from universities.models import University

from .services import representative_dashboard_context


@login_required
def home(request):
    if is_administrator(request.user):
        return redirect("dashboard:admin_home")
    return render(
        request,
        "dashboard/representative.html",
        representative_dashboard_context(request.user),
    )


@admin_required
def admin_home(request):
    pending = University.objects.pending().order_by("-created_at")
    now = timezone.now()
    recent_assessments = Assessment.objects.select_related("university")[:6]
    context = {
        "total_universities": University.objects.count(),
        "approved_universities": University.objects.approved().count(),
        "pending_universities": pending.count(),
        "total_assessments": Assessment.objects.count(),
        "assessments_this_month": Assessment.objects.filter(
            created_at__year=now.year, created_at__month=now.month
        ).count(),
        "total_resources": Resource.objects.count(),
        "published_resources": Resource.objects.filter(is_published=True).count(),
        "open_messages": ContactMessage.objects.filter(is_resolved=False).count(),
        "average_score": Assessment.objects.aggregate(value=Avg("overall_score"))["value"],
        "pending_list": pending[:5],
        "recent_assessments": recent_assessments,
        "recent_resources": Resource.objects.order_by("-updated_at")[:5],
        "category_counts": {
            label: (
                University.objects.approved()
                .filter(assessments__category=label)
                .distinct()
                .count()
            )
            for label in ["Initial", "Developing", "Advanced", "Leading"]
        },
    }
    return render(request, "dashboard/admin.html", context)

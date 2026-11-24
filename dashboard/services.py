from django.db.models import Avg, Max
from django.utils import timezone

from assessments.models import Assessment
from assessments.services import build_recommendations
from resources.models import Resource
from universities.models import University


def representative_dashboard_context(user):
    profile = user.profile
    university = profile.university
    assessments = (
        Assessment.objects.filter(university=university).order_by("-created_at")
        if university
        else Assessment.objects.none()
    )
    latest = assessments.first()
    previous = assessments[1] if assessments.count() > 1 else None
    delta = None
    if latest and previous:
        delta = float(latest.overall_score) - float(previous.overall_score)

    stats = assessments.aggregate(best=Max("overall_score"), avg=Avg("overall_score"))

    completion_items = [
        bool(profile.job_title),
        bool(profile.phone),
        bool(university and university.website),
        bool(university and len(university.description or "") >= 120),
        bool(university and university.city),
        bool(assessments.exists()),
    ]
    completion = round(sum(1 for item in completion_items if item) / len(completion_items) * 100)

    context = {
        "profile_obj": profile,
        "university": university,
        "latest": latest,
        "results": latest.ordered_results if latest else [],
        "recommendations": build_recommendations(latest) if latest else [],
        "assessment_history": assessments[:6],
        "assessment_count": assessments.count(),
        "best_score": stats["best"],
        "average_score": round(float(stats["avg"]), 1) if stats["avg"] is not None else None,
        "delta": delta,
        "last_assessed": latest.created_at if latest else None,
        "profile_completion": completion,
        "recent_resources": Resource.objects.filter(is_published=True)[:3],
        "category_counts": {
            label: assessments.filter(category=label).count()
            for label in ["Initial", "Developing", "Advanced", "Leading"]
        },
    }
    return context

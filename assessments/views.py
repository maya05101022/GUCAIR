from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import (
    admin_required,
    approved_university_required,
    is_administrator,
    representative_or_admin_required,
    representative_required,
)

from .forms import AssessmentForm
from .models import (
    DIMENSIONS,
    DIMENSION_LABELS,
    SCORE_CATEGORIES,
    Assessment,
    category_for_score,
)
from .questions_data import RESPONSE_SCALE
from .services import build_recommendations, create_assessment, get_active_questions


def _representative_queryset(user):
    if is_administrator(user):
        return Assessment.objects.all()
    university = getattr(user.profile, "university", None)
    if not university:
        return Assessment.objects.none()
    return Assessment.objects.filter(university=university)


@representative_required
def assessment_overview(request):
    university = request.user.profile.university
    assessments = Assessment.objects.filter(university=university)
    latest = assessments.first()
    active_questions = get_active_questions()
    context = {
        "university": university,
        "latest": latest,
        "results": latest.ordered_results if latest else [],
        "history": assessments[:5],
        "assessment_count": assessments.count(),
        "question_count": len(active_questions),
        "dimensions": DIMENSIONS,
        "scale": RESPONSE_SCALE,
        "categories": SCORE_CATEGORIES,
        "recommendations": build_recommendations(latest) if latest else [],
        "can_assess": university.is_approved,
    }
    return render(request, "assessments/overview.html", context)


@approved_university_required
def take_assessment(request):
    university = request.user.profile.university
    if request.method == "POST":
        form = AssessmentForm(request.POST)
        if form.is_valid():
            try:
                assessment = create_assessment(
                    university=university,
                    submitted_by=request.user,
                    answers=form.answers(),
                )
            except ValidationError as exc:
                messages.error(request, " ".join(exc.messages))
            else:
                messages.success(
                    request,
                    f"Assessment submitted. Overall readiness: "
                    f"{assessment.overall_score}% ({assessment.category}).",
                )
                return redirect("assessments:detail", pk=assessment.pk)
        else:
            messages.error(
                request,
                "Some responses are missing or invalid. Review the highlighted questions.",
            )
    else:
        form = AssessmentForm()

    return render(
        request,
        "assessments/take.html",
        {
            "form": form,
            "university": university,
            "groups": form.grouped_questions(),
            "scale": RESPONSE_SCALE,
            "question_count": len(form.questions),
        },
    )


@representative_required
def assessment_history(request):
    university = request.user.profile.university
    assessments = Assessment.objects.filter(university=university).order_by(
        "-created_at"
    )
    paginator = Paginator(assessments, 10)
    page = paginator.get_page(request.GET.get("page"))
    scores = [
        {
            "label": item.created_at.strftime("%d %b %Y"),
            "score": float(item.overall_score),
            "category": item.category,
        }
        for item in reversed(list(assessments[:12]))
    ]
    return render(
        request,
        "assessments/history.html",
        {
            "university": university,
            "page_obj": page,
            "assessments": page.object_list,
            "score_history": scores,
            "total": assessments.count(),
        },
    )


@representative_or_admin_required
def assessment_detail(request, pk):
    queryset = _representative_queryset(request.user).select_related(
        "university", "submitted_by"
    )
    assessment = get_object_or_404(queryset, pk=pk)
    previous = (
        Assessment.objects.filter(
            university=assessment.university, created_at__lt=assessment.created_at
        )
        .order_by("-created_at")
        .first()
    )
    delta = None
    if previous:
        delta = float(assessment.overall_score) - float(previous.overall_score)

    responses = list(
        assessment.responses.select_related("question").order_by(
            "question__dimension", "question__order"
        )
    )
    grouped_responses = []
    for key, label, _ in DIMENSIONS:
        items = [r for r in responses if r.question.dimension == key]
        if items:
            grouped_responses.append({"key": key, "label": label, "responses": items})

    results = list(assessment.ordered_results)
    category_colors = {
        "Initial": "#b23b3b",
        "Developing": "#b5852f",
        "Advanced": "#3d6f9e",
        "Leading": "#1f7a54",
    }
    return render(
        request,
        "assessments/detail.html",
        {
            "assessment": assessment,
            "university": assessment.university,
            "results": results,
            "responses": responses,
            "grouped_responses": grouped_responses,
            "recommendations": build_recommendations(assessment),
            "previous": previous,
            "delta": delta,
            "is_admin_view": is_administrator(request.user),
            "chart_data": {
                "labels": [
                    result.get_dimension_display().replace("AI ", "") for result in results
                ],
                "scores": [float(result.score) for result in results],
                "colors": [
                    category_colors.get(result.category, "#3d6f9e") for result in results
                ],
            },
        },
    )


@admin_required
def manage_assessments(request):
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "")
    assessments = Assessment.objects.select_related(
        "university", "submitted_by"
    ).order_by("-created_at")
    if q:
        assessments = assessments.filter(
            Q(university__name__icontains=q)
            | Q(university__country__icontains=q)
            | Q(submitted_by__username__icontains=q)
        )
    if category:
        assessments = assessments.filter(category=category)

    paginator = Paginator(assessments, 12)
    page = paginator.get_page(request.GET.get("page"))
    querystring = request.GET.copy()
    querystring.pop("page", None)
    return render(
        request,
        "assessments/manage.html",
        {
            "page_obj": page,
            "assessments": page.object_list,
            "q": q,
            "category": category,
            "categories": [label for _, _, label in SCORE_CATEGORIES],
            "total": assessments.count(),
            "querystring": querystring.urlencode(),
        },
    )


@require_POST
@admin_required
def delete_assessment(request, pk):
    assessment = get_object_or_404(Assessment, pk=pk)
    university = assessment.university.name
    assessment.delete()
    messages.success(
        request, f"Assessment record for {university} was permanently removed."
    )
    return redirect(request.POST.get("next") or "assessments:manage")

from collections import OrderedDict

from django.contrib.auth.models import User
from django.db.models import Avg, Count, OuterRef, Subquery
from django.db.models.functions import TruncMonth
from django.utils import timezone

from assessments.models import (
    DIMENSIONS,
    Assessment,
    AssessmentResult,
    DIMENSION_LABELS,
)
from universities.models import University


def latest_universities():
    """Approved universities annotated with their most recent assessment."""
    latest = Assessment.objects.filter(university=OuterRef("pk")).order_by(
        "-created_at", "-pk"
    )
    return (
        University.objects.approved()
        .annotate(
            latest_assessment_id=Subquery(latest.values("id")[:1]),
            latest_result_score=Subquery(latest.values("overall_score")[:1]),
            latest_result_category=Subquery(latest.values("category")[:1]),
            latest_result_date=Subquery(latest.values("created_at")[:1]),
            assessment_count=Count("assessments", distinct=True),
        )
        .order_by("name")
    )


def latest_assessment_ids(universities):
    return [u.latest_assessment_id for u in universities if u.latest_assessment_id]


def dimension_averages(latest_ids):
    raw = (
        AssessmentResult.objects.filter(assessment_id__in=latest_ids)
        .values("dimension")
        .annotate(avg=Avg("score"), n=Count("id"))
    )
    lookup = {row["dimension"]: row for row in raw}
    output = []
    for key, label, description in DIMENSIONS:
        row = lookup.get(key)
        output.append(
            {
                "key": key,
                "label": label,
                "short_label": label.replace("AI ", "").replace(" and ", " & "),
                "description": description,
                "average": round(float(row["avg"]), 1) if row and row["avg"] is not None else 0,
                "count": row["n"] if row else 0,
            }
        )
    return output


def category_distribution(universities):
    counts = OrderedDict((label, 0) for label in ["Initial", "Developing", "Advanced", "Leading"])
    for university in universities:
        if university.latest_result_category in counts:
            counts[university.latest_result_category] += 1
    total = sum(counts.values())
    return [
        {
            "label": label,
            "count": count,
            "percentage": round(count / total * 100, 1) if total else 0,
        }
        for label, count in counts.items()
    ]


def country_statistics(universities):
    grouped = {}
    for university in universities:
        bucket = grouped.setdefault(
            university.country, {"country": university.country, "count": 0, "assessed": 0, "scores": []}
        )
        bucket["count"] += 1
        if university.latest_result_score is not None:
            bucket["assessed"] += 1
            bucket["scores"].append(float(university.latest_result_score))
    rows = []
    for bucket in grouped.values():
        rows.append(
            {
                "country": bucket["country"],
                "count": bucket["count"],
                "assessed": bucket["assessed"],
                "average": round(sum(bucket["scores"]) / len(bucket["scores"]), 1)
                if bucket["scores"]
                else None,
            }
        )
    return sorted(rows, key=lambda row: (-row["count"], row["country"]))


def monthly_assessments(months=6):
    now = timezone.now()
    start = (now - timezone.timedelta(days=31 * (months - 1))).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    rows = (
        Assessment.objects.filter(created_at__gte=start, university__status=University.STATUS_APPROVED)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(total=Count("id"))
        .order_by("month")
    )
    lookup = {row["month"].strftime("%Y-%m"): row["total"] for row in rows}
    output = []
    cursor = start
    for _ in range(months):
        key = cursor.strftime("%Y-%m")
        output.append(
            {"label": cursor.strftime("%b %Y"), "count": lookup.get(key, 0)}
        )
        year = cursor.year + (1 if cursor.month == 12 else 0)
        month = 1 if cursor.month == 12 else cursor.month + 1
        cursor = cursor.replace(year=year, month=month, day=1)
    return output


def consortium_statistics():
    universities = list(latest_universities())
    assessed = [u for u in universities if u.latest_result_score is not None]
    latest_ids = latest_assessment_ids(universities)
    avg_score = (
        round(sum(float(u.latest_result_score) for u in assessed) / len(assessed), 1)
        if assessed
        else 0
    )
    return {
        "universities": universities,
        "total_universities": len(universities),
        "assessed_universities": len(assessed),
        "total_assessments": Assessment.objects.filter(
            university__status=University.STATUS_APPROVED
        ).count(),
        "total_representatives": User.objects.filter(
            profile__role="representative"
        ).count(),
        "countries": len({u.country for u in universities}),
        "average_score": avg_score,
        "average_category": _category_for(avg_score),
        "dimensions": dimension_averages(latest_ids),
        "categories": category_distribution(universities),
        "by_country": country_statistics(universities),
        "monthly": monthly_assessments(),
        "top_universities": sorted(
            assessed, key=lambda u: float(u.latest_result_score), reverse=True
        )[:5],
        "latest_ids": latest_ids,
        "demo_count": sum(1 for u in universities if u.is_demo),
    }


def public_statistics():
    universities = University.objects.approved()
    latest = (
        Assessment.objects.filter(university__status=University.STATUS_APPROVED)
        .order_by("university_id", "-created_at")
    )
    # Latest score per university without database-specific DISTINCT ON.
    seen = {}
    for item in latest:
        seen.setdefault(item.university_id, item)
    scores = [float(item.overall_score) for item in seen.values()]
    total_universities = universities.count()
    return {
        "university_count": total_universities,
        "country_count": universities.values("country").distinct().count(),
        "assessment_count": Assessment.objects.filter(
            university__status=University.STATUS_APPROVED
        ).count(),
        "average_score": round(sum(scores) / len(scores), 1) if scores else 0,
        "assessment_coverage": round(len(scores) / total_universities * 100)
        if total_universities
        else 0,
        # `seen` is keyed by university id, so pass the latest assessment ids.
        "dimensions": dimension_averages([item.pk for item in seen.values()]),
    }


def _category_for(score):
    if score < 40:
        return "Initial"
    if score < 60:
        return "Developing"
    if score < 80:
        return "Advanced"
    return "Leading"


def comparison_data(universities):
    """Build chart-ready comparison rows for selected universities."""
    rows = []
    for university in universities:
        latest = (
            Assessment.objects.filter(university=university)
            .order_by("-created_at")
            .first()
        )
        if not latest:
            continue
        dimension_map = {
            item.dimension: float(item.score) for item in latest.results.all()
        }
        rows.append(
            {
                "university": university,
                "assessment": latest,
                "overall": float(latest.overall_score),
                "category": latest.category,
                "dimensions": [
                    {
                        "key": key,
                        "label": DIMENSION_LABELS.get(key, key),
                        "short_label": DIMENSION_LABELS.get(key, key)
                        .replace("AI ", "")
                        .replace(" and ", " & "),
                        "score": dimension_map.get(key, 0),
                    }
                    for key, _, _ in DIMENSIONS
                ],
            }
        )
    return rows

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render

from .services import comparison_data, consortium_statistics, latest_universities


@login_required
def analytics_dashboard(request):
    stats = consortium_statistics()
    return render(request, "analytics/dashboard.html", {"stats": stats})


@login_required
def comparison(request):
    all_universities = latest_universities()
    selected_ids = []
    for value in request.GET.getlist("u"):
        try:
            selected_ids.append(int(value))
        except (TypeError, ValueError):
            continue
    selected_ids = selected_ids[:5]

    selectable = list(all_universities)
    selected = [u for u in selectable if u.pk in selected_ids]
    rows = comparison_data(selected) if len(selected) >= 1 else []
    countries = sorted({u.country for u in selectable})

    chart = {
        # Keep the axis readable inside the narrow chart card.
        "labels": [
            row["university"].name
            if len(row["university"].name) <= 26
            else row["university"].name[:25] + "…"
            for row in rows
        ],
        "overall": [row["overall"] for row in rows],
        "dimension_labels": [item["short_label"] for item in rows[0]["dimensions"]]
        if rows
        else [],
        "dimension_datasets": [
            {
                "label": row["university"].name,
                "data": [item["score"] for item in row["dimensions"]],
            }
            for row in rows
        ],
    }
    return render(
        request,
        "analytics/comparison.html",
        {
            "universities": selectable,
            "selected": selected,
            "rows": rows,
            "selected_ids": [u.pk for u in selected],
            "chart": chart,
            "countries": countries,
            "too_many": len(request.GET.getlist("u")) > 5,
        },
    )


def public_stats_api(request):
    """Small read-only JSON endpoint used to verify production data access."""
    stats = consortium_statistics()
    return JsonResponse(
        {
            "approved_universities": stats["total_universities"],
            "completed_assessments": stats["total_assessments"],
            "average_readiness": stats["average_score"],
            "countries": stats["countries"],
        }
    )

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import connection
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import admin_required
from analytics.services import public_statistics
from assessments.models import DIMENSIONS, Assessment
from resources.models import Resource
from universities.models import COUNTRIES, University

from .forms import ContactForm
from .models import ContactMessage


def landing(request):
    stats = public_statistics()
    universities = University.objects.approved().order_by("name")[:8]
    resources = Resource.objects.filter(is_published=True)[:3]
    latest_scores = []
    for university in universities:
        latest_scores.append(
            {
                "university": university,
                "assessment": university.assessments.order_by("-created_at").first(),
            }
        )
    return render(
        request,
        "core/landing.html",
        {
            "stats": stats,
            "universities": latest_scores,
            "resources": resources,
            "dimensions": DIMENSIONS,
            "countries": COUNTRIES,
            "demo_count": University.objects.filter(is_demo=True, status="approved").count(),
        },
    )


def about(request):
    return render(
        request,
        "core/about.html",
        {"dimensions": DIMENSIONS, "stats": public_statistics()},
    )


def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Thank you. Your message has been recorded and the consortium "
                "secretariat will review it.",
            )
            return redirect("core:contact")
        messages.error(request, "Please correct the highlighted fields.")
    else:
        form = ContactForm()
    return render(request, "core/contact.html", {"form": form})


@admin_required
def contact_messages(request):
    query = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    queryset = ContactMessage.objects.all()
    if query:
        queryset = queryset.filter(
            Q(name__icontains=query)
            | Q(email__icontains=query)
            | Q(subject__icontains=query)
            | Q(message__icontains=query)
        )
    if status == "open":
        queryset = queryset.filter(is_resolved=False)
    elif status == "resolved":
        queryset = queryset.filter(is_resolved=True)
    paginator = Paginator(queryset, 10)
    page = paginator.get_page(request.GET.get("page"))
    return render(
        request,
        "core/contact_messages.html",
        {
            "page_obj": page,
            "messages_list": page.object_list,
            "q": query,
            "status": status,
            "total": queryset.count(),
            "open_count": ContactMessage.objects.filter(is_resolved=False).count(),
        },
    )


@require_POST
@admin_required
def toggle_contact_message(request, pk):
    message = get_object_or_404(ContactMessage, pk=pk)
    message.is_resolved = not message.is_resolved
    message.save(update_fields=["is_resolved"])
    messages.success(
        request,
        f"Message marked as {'resolved' if message.is_resolved else 'open'}.",
    )
    return redirect("core:contact_messages")


def health(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return JsonResponse(
            {
                "status": "ok",
                "database": "connected",
                "universities": University.objects.count(),
                "assessments": Assessment.objects.count(),
            }
        )
    except Exception:
        return JsonResponse({"status": "error", "database": "unavailable"}, status=503)


def error_404(request, exception):
    return render(request, "errors/404.html", status=404)


def error_500(request):
    return render(request, "errors/500.html", status=500)

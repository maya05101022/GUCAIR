from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from accounts.decorators import admin_required, is_administrator

from .forms import ResourceForm
from .models import Resource


def resource_list(request):
    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "")
    resources = Resource.objects.filter(is_published=True)
    if q:
        resources = resources.filter(
            Q(title__icontains=q) | Q(summary__icontains=q) | Q(content__icontains=q)
        )
    if category in dict(Resource.CATEGORY_CHOICES):
        resources = resources.filter(category=category)

    paginator = Paginator(resources, 9)
    page = paginator.get_page(request.GET.get("page"))
    querystring = request.GET.copy()
    querystring.pop("page", None)
    return render(
        request,
        "resources/list.html",
        {
            "page_obj": page,
            "resources": page.object_list,
            "q": q,
            "category": category,
            "categories": Resource.CATEGORY_CHOICES,
            "total": resources.count(),
            "querystring": querystring.urlencode(),
        },
    )


def resource_detail(request, slug):
    resource = get_object_or_404(Resource, slug=slug)
    if not resource.is_published and not (
        request.user.is_authenticated and is_administrator(request.user)
    ):
        raise Http404("Resource not found")
    related = (
        Resource.objects.filter(is_published=True, category=resource.category)
        .exclude(pk=resource.pk)[:3]
    )
    return render(
        request,
        "resources/detail.html",
        {"resource": resource, "related": related},
    )


@admin_required
def manage_resources(request):
    q = request.GET.get("q", "").strip()
    status = request.GET.get("status", "")
    category = request.GET.get("category", "")
    resources = Resource.objects.select_related("created_by").all()
    if q:
        resources = resources.filter(Q(title__icontains=q) | Q(summary__icontains=q))
    if status == "published":
        resources = resources.filter(is_published=True)
    elif status == "draft":
        resources = resources.filter(is_published=False)
    if category in dict(Resource.CATEGORY_CHOICES):
        resources = resources.filter(category=category)

    paginator = Paginator(resources, 10)
    page = paginator.get_page(request.GET.get("page"))
    querystring = request.GET.copy()
    querystring.pop("page", None)
    return render(
        request,
        "resources/manage.html",
        {
            "page_obj": page,
            "resources": page.object_list,
            "q": q,
            "status": status,
            "category": category,
            "categories": Resource.CATEGORY_CHOICES,
            "total": resources.count(),
            "querystring": querystring.urlencode(),
        },
    )


@admin_required
def resource_create(request):
    if request.method == "POST":
        form = ResourceForm(request.POST)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.created_by = request.user
            resource.save()
            messages.success(request, "Resource published to the AI Resource Hub.")
            return redirect("resources:manage")
        messages.error(request, "Please correct the highlighted fields.")
    else:
        form = ResourceForm()
    return render(
        request,
        "resources/form.html",
        {"form": form, "is_create": True},
    )


@admin_required
def resource_edit(request, slug):
    resource = get_object_or_404(Resource, slug=slug)
    if request.method == "POST":
        form = ResourceForm(request.POST, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, "Resource updated.")
            return redirect("resources:manage")
        messages.error(request, "Please correct the highlighted fields.")
    else:
        form = ResourceForm(instance=resource)
    return render(
        request,
        "resources/form.html",
        {"form": form, "resource": resource, "is_create": False},
    )


@require_POST
@admin_required
def resource_delete(request, slug):
    resource = get_object_or_404(Resource, slug=slug)
    title = resource.title
    resource.delete()
    messages.success(request, f"Resource “{title}” was deleted.")
    return redirect("resources:manage")

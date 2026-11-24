from django.contrib import admin

from .models import (
    Assessment,
    AssessmentQuestion,
    AssessmentResponse,
    AssessmentResult,
)


class AssessmentResultInline(admin.TabularInline):
    model = AssessmentResult
    extra = 0
    readonly_fields = ("dimension", "score", "raw_score", "max_score")


@admin.register(AssessmentQuestion)
class AssessmentQuestionAdmin(admin.ModelAdmin):
    list_display = ("text", "dimension", "order", "is_active")
    list_filter = ("dimension", "is_active")
    search_fields = ("text", "guidance")
    ordering = ("dimension", "order")


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("university", "overall_score", "category", "submitted_by", "created_at")
    list_filter = ("category", "created_at", "university__country")
    search_fields = ("university__name", "submitted_by__username")
    readonly_fields = (
        "university",
        "submitted_by",
        "overall_score",
        "category",
        "total_raw_score",
        "max_raw_score",
        "created_at",
    )
    inlines = [AssessmentResultInline]


@admin.register(AssessmentResponse)
class AssessmentResponseAdmin(admin.ModelAdmin):
    list_display = ("assessment", "question", "score")
    list_filter = ("question__dimension",)


@admin.register(AssessmentResult)
class AssessmentResultAdmin(admin.ModelAdmin):
    list_display = ("assessment", "dimension", "score", "raw_score", "max_score")
    list_filter = ("dimension",)

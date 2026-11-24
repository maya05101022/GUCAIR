from django.contrib import admin

from .models import University


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "city", "status", "is_demo", "created_at")
    list_filter = ("status", "country", "is_demo")
    search_fields = ("name", "city", "country", "description")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("created_at", "updated_at", "approved_at")

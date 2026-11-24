from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from .models import UserProfile


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 0


class UserAdmin(BaseUserAdmin):
    inlines = [UserProfileInline]
    list_display = ("username", "email", "get_full_name", "get_role", "is_active")
    list_filter = ("is_active", "is_staff", "profile__role")

    @admin.display(description="Role")
    def get_role(self, obj):
        return getattr(obj.profile, "role", "—")


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(UserProfile)

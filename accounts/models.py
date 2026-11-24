from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    """Extra account data attached to Django's built-in User model."""

    ROLE_ADMIN = "admin"
    ROLE_REPRESENTATIVE = "representative"
    ROLE_CHOICES = [
        (ROLE_ADMIN, "Administrator"),
        (ROLE_REPRESENTATIVE, "University Representative"),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile"
    )
    role = models.CharField(
        max_length=20, choices=ROLE_CHOICES, default=ROLE_REPRESENTATIVE
    )
    job_title = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    university = models.ForeignKey(
        "universities.University",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="representatives",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["user__first_name", "user__last_name", "user__username"]
        verbose_name = "User profile"
        verbose_name_plural = "User profiles"

    def __str__(self) -> str:
        return f"{self.display_name} ({self.get_role_display()})"

    @property
    def display_name(self) -> str:
        full_name = self.user.get_full_name().strip()
        return full_name or self.user.username

    @property
    def is_administrator(self) -> bool:
        return self.role == self.ROLE_ADMIN or self.user.is_superuser

    @property
    def is_representative(self) -> bool:
        return self.role == self.ROLE_REPRESENTATIVE

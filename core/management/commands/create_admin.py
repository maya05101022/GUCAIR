"""Create or update the production administrator from environment variables.

Required environment variables:
    ADMIN_USERNAME
    ADMIN_PASSWORD
    ADMIN_EMAIL (optional)

Running this command repeatedly is safe; the password is synchronised only
when ADMIN_PASSWORD is explicitly provided.
"""

import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Idempotently create the GUCAIR administrator from environment variables."

    def handle(self, *args, **options):
        username = (os.environ.get("ADMIN_USERNAME") or "").strip()
        password = os.environ.get("ADMIN_PASSWORD") or ""
        email = (os.environ.get("ADMIN_EMAIL") or "").strip()

        if not username or not password:
            self.stdout.write(
                self.style.WARNING(
                    "ADMIN_USERNAME and ADMIN_PASSWORD are not both set; "
                    "skipping administrator bootstrap."
                )
            )
            return

        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "first_name": "GUCAIR", "last_name": "Administrator"},
        )
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        if email:
            user.email = email
        user.set_password(password)
        user.save()

        from accounts.models import UserProfile

        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.role = UserProfile.ROLE_ADMIN
        profile.save(update_fields=["role"])

        state = "created" if created else "updated"
        self.stdout.write(
            self.style.SUCCESS(f"Administrator '{username}' {state} successfully.")
        )

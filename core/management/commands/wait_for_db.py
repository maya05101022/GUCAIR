import time

from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = "Wait for the configured database to accept connections."

    def handle(self, *args, **options):
        attempts = 30
        for attempt in range(1, attempts + 1):
            try:
                connection.ensure_connection()
                self.stdout.write(self.style.SUCCESS("Database connection established."))
                return
            except OperationalError:
                self.stdout.write(
                    f"Database unavailable ({attempt}/{attempts}); retrying in 2 seconds…"
                )
                time.sleep(2)
        raise SystemExit("Database did not become available in time.")

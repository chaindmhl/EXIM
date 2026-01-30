from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.utils import OperationalError
import time

class Command(BaseCommand):
    help = "Creates a superuser if none exists"

    def handle(self, *args, **options):
        User = get_user_model()
        retries = 10
        for i in range(retries):
            try:
                if not User.objects.filter(is_superuser=True).exists():
                    User.objects.create_superuser(
                        email="admin@example.com",
                        password="admin@03"
                    )
                    self.stdout.write(self.style.SUCCESS("Superuser created"))
                else:
                    self.stdout.write(self.style.SUCCESS("Superuser already exists"))
                break
            except OperationalError:
                self.stdout.write(f"Database not ready, retrying {i+1}/{retries}")
                time.sleep(3)

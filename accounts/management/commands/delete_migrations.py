import os
import platform
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Deletes all migration files except __init__.py files'

    def handle(self, *args, **options):
        # Delete migration files except __init__.py
        self.stdout.write("Deleting migration files...")
        
        if platform.system() == 'Darwin':  # macOS
            os.system("find . -path '*/migrations/*.py' -not -path '*/.venv/*' -not -name '__init__.py' -delete")
            os.system("find . -path '*/migrations/*.pyc' -not -path '*/.venv/*' -delete")
        else:
            self.stdout.write(self.style.ERROR("Unsupported operating system."))

        self.stdout.write(self.style.SUCCESS("Migration files deleted successfully."))
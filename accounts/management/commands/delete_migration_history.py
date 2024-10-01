from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Deletes migration history entries from the database'

    def handle(self, *args, **kwargs):
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM django_migrations")
        
        self.stdout.write(self.style.SUCCESS('Migration history has been deleted successfully.'))

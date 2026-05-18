import psutil
from django.core.management import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        print(psutil.Process().memory_full_info())

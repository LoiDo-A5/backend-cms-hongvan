import logging
import os

from django.db.migrations.recorder import MigrationRecorder

from common.management.commands.django_base import DjangoCommand

logger = logging.getLogger(__name__)


class Command(DjangoCommand):
    def handle(self, *args, **options):
        self.fix_migration_entries()

    def fix_migration_entries(self):
        apps = list(self.get_local_apps())
        local_apps = [x.label for x in apps]
        MigrationRecorder.Migration.objects.all().filter(app__in=local_apps).delete()
        for app in apps:
            migrations_path = os.path.join(app.path, 'migrations')

            try:
                dir_entries = os.scandir(migrations_path)
            except FileNotFoundError:
                continue

            for dir_entry in dir_entries:
                if dir_entry.name == '__init__.py':
                    continue
                if not dir_entry.name.endswith('.py'):
                    continue
                MigrationRecorder.Migration.objects.create(
                    app=app.label,
                    name=dir_entry.name.split('.')[0],
                )

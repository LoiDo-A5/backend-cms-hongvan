import logging
import os

from django.core.management import call_command

from common.management.commands.django_base import DjangoCommand

logger = logging.getLogger(__name__)


class Command(DjangoCommand):
    def handle(self, *args, **options):
        self.delete_all_migrations()
        call_command('makemigrations')
        call_command('re_init_migration')

    def delete_all_migrations(self):
        for app in self.get_local_apps():

            migrations_path = os.path.join(app.path, 'migrations')
            if not os.path.isdir(migrations_path):
                continue

            dir_entries = os.scandir(migrations_path)
            for dir_entry in dir_entries:
                if dir_entry.is_dir():
                    continue
                if dir_entry.name == '__init__.py':
                    continue
                os.unlink(dir_entry.path)
            logger.info(migrations_path)

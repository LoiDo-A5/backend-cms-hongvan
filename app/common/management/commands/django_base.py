import logging
import os

from django.apps import apps
from django.conf import settings
from django.core.management import BaseCommand

logger = logging.getLogger(__name__)


class DjangoCommand(BaseCommand):
    def get_local_apps(self):
        root = settings.BASE_DIR
        for app in apps.get_app_configs():
            path = app.module.__name__.replace('.', '/')
            abs_path = os.path.join(root, path)
            if not os.path.isdir(abs_path):
                continue
            yield app

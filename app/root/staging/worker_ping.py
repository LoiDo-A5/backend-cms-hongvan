from .web import *  # noqa

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',

    'common',
    'core.accounts',
]

ROOT_URLCONF = 'root.empty_urls'

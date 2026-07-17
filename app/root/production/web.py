from root.settings import *  # noqa

IS_PRODUCTION = True

STATIC_ROOT = '/app/static'
STATIC_URL = '/static/'

MEDIA_ROOT = '/media'
MEDIA_URL = '/media/'

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
    },
}
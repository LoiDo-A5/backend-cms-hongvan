from root.settings import *  # noqa

API_DOCUMENT = True

# s3 static settings
STATIC_LOCATION = 'static'
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{STATIC_LOCATION}/'
# s3 public media settings
PUBLIC_MEDIA_LOCATION = 'media'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{PUBLIC_MEDIA_LOCATION}/'

STORAGES = {
    'default': {
        'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
    },
    'staticfiles': {
        'BACKEND': 'storages.backends.s3boto3.S3Boto3Storage',
    },
}

LOCATION_FIELD_PATH = f'https://{AWS_S3_CUSTOM_DOMAIN}/location_field'
LOCATION_FIELD['resources.media']['js'] = (
    LOCATION_FIELD_PATH + '/js/form.js',
)
LOCATION_FIELD['resources.root_path'] = LOCATION_FIELD_PATH

# ddtrace
from ddtrace import config, tracer
tracer.set_tags({'env': 'staging'})

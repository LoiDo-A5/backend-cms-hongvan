from django.urls import path
from rest_framework import routers

from common.api.config import ConfigApi
from common.api.s3_presigned import S3PresignedApi

router = routers.SimpleRouter()

urlpatterns = [
    path('config/ios/', ConfigApi.as_view(platform='IOS')),
    path('config/android/', ConfigApi.as_view(platform='ANDROID')),
    path('s3_presigned/', S3PresignedApi.as_view()),
]

urlpatterns += router.urls

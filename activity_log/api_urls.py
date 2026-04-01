from django.urls import path

from activity_log.api.certificate_export_log import CertificateExportLogApi
from activity_log.api.certificate_verify_log import CertificateVerifyLogApi
from activity_log.api.artwork_log import ArtworkActivityLogApi

urlpatterns = [
    path('certificate_export_logs/', CertificateExportLogApi.as_view()),
    path('certificate_verify_logs/', CertificateVerifyLogApi.as_view()),
    path('artwork_logs/', ArtworkActivityLogApi.as_view(), name='artwork-activity-logs'),
]

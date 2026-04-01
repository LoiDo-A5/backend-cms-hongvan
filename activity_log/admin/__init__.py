from django.contrib import admin

import activity_log.admin.artwork_log_admin  # noqa: F401
from activity_log.admin.certificate_log_admin import CertificateLogAdmin
from activity_log.models.certificate_log import CertificateLog
from activity_log.admin.artwork_log_admin import ArtworkLogAdmin
from activity_log.models.artwork_log import ArtworkLog

admin.site.register(CertificateLog, CertificateLogAdmin)
admin.site.register(ArtworkLog, ArtworkLogAdmin)

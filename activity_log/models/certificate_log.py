from django.db import models

from artwork.models import ArtworkCertificate
from artwork.utils.const import ACTION_CHOICES, EXPORT
from common.abstract_models.image_field import CustomImageField


class CertificateLog(models.Model):
    user = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE,
        null=True, blank=True, related_name='certificate_logs',
    )
    certificate = models.ForeignKey(ArtworkCertificate, on_delete=models.CASCADE,
                                    null=True, blank=True, related_name='logs',
                                    )
    data = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    image = CustomImageField(blank=True, null=True)
    action_type = models.CharField(
        choices=ACTION_CHOICES,
        default=EXPORT,
    )

    class Meta:
        ordering = (
            '-created_at',
        )

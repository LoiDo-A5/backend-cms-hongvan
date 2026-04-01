from django.db import models
import uuid

from artwork.utils.const import PROCESSING_STATUS_CHOICES
from common.abstract_models.image_field import CustomImageField


class ArtworkCertificate(models.Model):
    artwork_edition = models.OneToOneField('artwork.ArtworkEdition', on_delete=models.SET_NULL, null=True,
                                           blank=True, related_name='certificate',
                                           )
    issued_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE, null=True,
                                  related_name='issued_certificates')
    issued_to = models.ForeignKey('accounts.User', on_delete=models.CASCADE, null=True, blank=True,
                                  related_name='owned_certificates')
    code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    signature = CustomImageField(blank=True, null=True)
    status = models.CharField(max_length=255, choices=PROCESSING_STATUS_CHOICES,
                              default='', blank=True, null=True)

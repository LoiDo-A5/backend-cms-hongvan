from django.db import models

from artwork.models import CertificateRequest
from common.abstract_models.image_field import CustomImageField


class ImageCertificateRequest(models.Model):
    certificate_request = models.ForeignKey(CertificateRequest, on_delete=models.CASCADE, null=True)
    image = CustomImageField(blank=False)

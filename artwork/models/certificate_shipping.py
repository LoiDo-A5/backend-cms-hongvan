from django.db import models


class CertificateShipping(models.Model):
    certificate = models.OneToOneField('artwork.ArtworkCertificate', on_delete=models.CASCADE,
                                       related_name='certificate_shipping')
    recipient = models.CharField(max_length=80)
    address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

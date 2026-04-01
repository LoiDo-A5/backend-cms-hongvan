from django.db import models


class OwnerCertificate(models.Model):
    certificate = models.OneToOneField('artwork.ArtworkCertificate', on_delete=models.CASCADE, related_name='owner')
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='owner_certificates',
    )
    name = models.CharField(max_length=50)
    year_of_birth = models.IntegerField(null=True, blank=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    contract_number = models.CharField(max_length=50, blank=True, null=True)

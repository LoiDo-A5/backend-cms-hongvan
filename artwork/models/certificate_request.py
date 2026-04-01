from django.db import models


class STATUS:
    REQUEST_RECEIVED = 1
    REQUEST_APPROVED = 2
    REQUEST_DENIED = 3


STATUS_CHOICES = (
    (STATUS.REQUEST_RECEIVED, 'Request received'),
    (STATUS.REQUEST_APPROVED, 'Request approved'),
    (STATUS.REQUEST_DENIED, 'Request denied'),
)


class CertificateRequest(models.Model):
    artwork_edition = models.OneToOneField('artwork.ArtworkEdition', on_delete=models.CASCADE,
                                           related_name='certificate_requests')
    request_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE,
                                   related_name='certificate_requests_made')
    request_to = models.ForeignKey('accounts.User', on_delete=models.CASCADE,
                                   related_name='certificate_requests_received')
    status = models.IntegerField(max_length=255, choices=STATUS_CHOICES,
                                 blank=True, null=True, default=1)
    owner_info = models.JSONField(null=True, blank=True)
    shipping_info = models.JSONField(null=True, blank=True)
    message = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

from django.db import models

from artwork.models import ArtWork
from artwork.models import ArtworkCertificate
from artwork.models import CertificateRequest
from core.accounts.models.user import USER_ROLE_CHOICES


class UserInvitation(models.Model):
    sender = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='sent_invitations')
    recipient = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='received_invitations')
    artwork = models.ForeignKey(ArtWork, on_delete=models.SET_NULL, null=True, blank=True)
    certificate = models.ForeignKey(ArtworkCertificate, on_delete=models.CASCADE, null=True, blank=True)
    certificate_request = models.ForeignKey(CertificateRequest, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    email = models.EmailField(null=True, blank=True)
    role_recipient = models.IntegerField(
        choices=USER_ROLE_CHOICES,
        blank=True,
        null=True,
    )

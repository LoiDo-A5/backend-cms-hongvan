from django.db import models

from core.accounts.models import User

from .artwork import ArtWork
from .artwork_certificate import ArtworkCertificate


class CollectorOwnershipTransfer(models.Model):
    """Audit row when a collector transfers artwork ownership (certificate or full edit flow)."""

    transferrer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='collector_ownership_transfers_sent',
    )
    transferee = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='collector_ownership_transfers_received',
    )
    artwork = models.ForeignKey(
        ArtWork,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='collector_ownership_transfers',
    )
    certificate = models.ForeignKey(
        ArtworkCertificate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='collector_ownership_transfers',
    )
    snapshot = models.JSONField()
    transferred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-transferred_at', '-id')
        indexes = [
            models.Index(fields=['transferrer', '-transferred_at']),
        ]

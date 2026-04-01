from django.db import models

from artwork.utils.const import STATUS_CHOICES
from artwork.models.artwork import CURRENCY_CHOICES
from core.accounts.models import User, UserLocation


class ArtworkEdition(models.Model):
    artwork = models.ForeignKey('artwork.ArtWork', on_delete=models.CASCADE, related_name='editions')
    edition_number = models.IntegerField()
    owner_name = models.CharField(max_length=100, blank=True, null=True)
    currency = models.CharField(max_length=5, choices=CURRENCY_CHOICES, default='vnd', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=255, choices=STATUS_CHOICES, default='', blank=True, null=True)
    location = models.ForeignKey(UserLocation, on_delete=models.SET_NULL, null=True, blank=True)
    linked_edition = models.OneToOneField('self', on_delete=models.SET_NULL, null=True, blank=True,
                                          related_name='linked_edition_related')
    transferee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='artwork_edition_transfers_received',
        help_text='User who received this edition when the artist transferred ownership.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (
            ('artwork', 'edition_number'),
        )

    def __str__(self):  # pragma: nocover
        return f'id:{self.id} | number:{self.edition_number}'

    def has_certificate(self):
        if hasattr(self, 'certificate'):
            return True
        linked = getattr(self, 'linked_edition', None)
        if linked and hasattr(linked, 'certificate'):
            return True
        reverse_linked = getattr(self, 'linked_edition_related', None)
        if reverse_linked and hasattr(reverse_linked, 'certificate'):
            return True
        return False

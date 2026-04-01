from django.db import models

from artwork.models import ArtWork


ACTION_UPDATE_ARTWORK = 'artwork_updated'
ACTION_CERTIFICATE_ISSUED = 'certificate_issued'
ACTION_CERTIFICATE_REQUESTED = 'certificate_requested'
ACTION_CERTIFICATE_REJECT = 'certificate_reject'
ACTION_ARTWORK_UPLOADED = 'artwork_uploaded'

ARTWORK_ACTION_CHOICES = [
    (ACTION_UPDATE_ARTWORK, 'Artwork Updated'),
    (ACTION_CERTIFICATE_ISSUED, 'Certificate Issued'),
    (ACTION_CERTIFICATE_REQUESTED, 'Certificate Requested'),
    (ACTION_CERTIFICATE_REJECT, 'Certificate Rejected'),
    (ACTION_ARTWORK_UPLOADED, 'Artwork Uploaded'),
]


class ArtworkLog(models.Model):
    artwork = models.ForeignKey(
        ArtWork,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activity_logs',
        help_text='The artwork this log entry is related to',
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='artwork_logs',
        help_text='User who performed the action',
    )
    action_type = models.CharField(
        max_length=50,
        choices=ARTWORK_ACTION_CHOICES,
        help_text='Type of action performed',
    )
    template_vi = models.TextField(
        null=True,
        blank=True,
        help_text='Vietnamese template at the time of logging',
    )
    template_en = models.TextField(
        null=True,
        blank=True,
        help_text='English template at the time of logging',
    )
    content_vi = models.TextField(
        default='',
        help_text='Snapshot Vietnamese content at the time of logging',
    )
    content_en = models.TextField(
        default='',
        help_text='Snapshot English content at the time of logging',
    )
    params = models.JSONField(
        default=dict,
        blank=True,
        help_text='Arbitrary parameters snapshot (e.g., old/new values, field names)',
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When this action was performed',
    )

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'Artwork Activity Log'
        verbose_name_plural = 'Artwork Activity Logs'
        indexes = [
            models.Index(fields=['artwork', '-created_at']),
            models.Index(fields=['-created_at']),
            models.Index(fields=['action_type']),
        ]

    def __str__(self):
        # Be robust if artwork is None (e.g., when logging deletion events)
        if self.artwork is None:
            title = 'Deleted Artwork'
        else:
            title = getattr(self.artwork, 'title', None) or f"Artwork #{getattr(self.artwork, 'pk', '?')}"
        return f'[{self.created_at}] {title}: {self.action_type}'

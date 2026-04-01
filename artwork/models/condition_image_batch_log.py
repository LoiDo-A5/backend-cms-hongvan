from django.db import models
from django.utils import timezone

from artwork.models.condition_image_batch import ConditionImageBatch
from artwork.models.artwork import ArtWork
from core.accounts.models import User


class ConditionImageBatchLog(models.Model):
    batch = models.ForeignKey(ConditionImageBatch, on_delete=models.CASCADE, related_name='logs')
    artwork = models.ForeignKey(ArtWork, on_delete=models.CASCADE, related_name='condition_image_logs')
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='condition_image_logs')
    images_snapshot = models.JSONField(default=list)
    update_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ('created_at', 'id')
        indexes = [
            models.Index(fields=['artwork', 'created_at']),
            models.Index(fields=['batch', 'created_at']),
        ]

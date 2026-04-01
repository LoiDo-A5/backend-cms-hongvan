from django.db import models
from django.utils import timezone

from core.accounts.models import User
from artwork.models.artwork import ArtWork
from common.abstract_models.image_field import CustomImageField


class ConditionImageBatch(models.Model):
    artwork = models.ForeignKey(ArtWork, on_delete=models.CASCADE, related_name='condition_image_batches')
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='condition_image_batches')
    created_at = models.DateTimeField(default=timezone.now)
    update_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('created_at', 'id')


class ConditionImage(models.Model):
    batch = models.ForeignKey(ConditionImageBatch, on_delete=models.CASCADE, related_name='images')
    image = CustomImageField(blank=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('order', 'id')

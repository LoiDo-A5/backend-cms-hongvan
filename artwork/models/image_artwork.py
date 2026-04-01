from django.db import models

from artwork.models import ArtWork
from common.abstract_models.image_field import CustomImageField


class ImageArtwork(models.Model):
    artwork = models.ForeignKey(ArtWork, on_delete=models.CASCADE, null=True)
    image = CustomImageField(blank=False)

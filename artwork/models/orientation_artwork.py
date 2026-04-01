from django.db import models

from artwork.utils.const import CATEGORY_CHOICES


class OrientationArtwork(models.Model):
    name = models.CharField(max_length=100)
    name_vi = models.CharField(max_length=100, blank=True, null=True)
    category = models.CharField(max_length=255, choices=CATEGORY_CHOICES, null=True)

    def __str__(self):  # pragma: nocover
        return str(self.name)

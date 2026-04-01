from django.db import models

from artwork.utils.const import CATEGORY_CHOICES


class ColorArtwork(models.Model):
    name = models.CharField(max_length=50)
    category = models.CharField(max_length=255, choices=CATEGORY_CHOICES, null=True)

    def __str__(self):  # pragma: nocover
        return str(self.name)

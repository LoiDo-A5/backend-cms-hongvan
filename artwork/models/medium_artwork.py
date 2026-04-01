from django.db import models

from artwork.utils.const import CATEGORY_CHOICES


class MediumArtwork(models.Model):
    name = models.CharField(max_length=100)
    name_vi = models.CharField(max_length=100, blank=True, null=True)
    category = models.CharField(max_length=255, choices=CATEGORY_CHOICES, null=True)
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, null=True, blank=True,
                             related_name='mediums')

    def __str__(self):  # pragma: nocover
        return str(self.name)

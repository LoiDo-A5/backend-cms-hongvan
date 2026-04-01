from django.db import models

from core.accounts.models import User


class ArtworkArtist(models.Model):
    create_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    artist_name = models.CharField(max_length=100, blank=True, null=True)
    contact_info = models.CharField(max_length=100, blank=True, null=True)
    year_of_birth = models.CharField(max_length=4, blank=True, null=True)
    year_of_death = models.CharField(max_length=4, blank=True, null=True)

    def __str__(self):  # pragma: nocover
        return self.artist_name

    class Meta:
        unique_together = (
            ('artist_name', 'year_of_birth', 'create_user'),
        )

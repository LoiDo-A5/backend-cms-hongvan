from django.db import models


class LikeArtwork(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='like_artworks')
    artwork = models.ForeignKey('artwork.ArtWork', on_delete=models.CASCADE, related_name='like_artworks')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):  # pragma: nocover
        return f'{self.id}'

    class Meta:
        unique_together = ('user', 'artwork')

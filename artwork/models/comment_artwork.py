from django.db import models

from artwork.models import ArtWork


class CommentArtwork(models.Model):
    artwork = models.ForeignKey(
        ArtWork,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='artwork_comments',
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_hidden = models.BooleanField(default=False, db_index=True)

    def __str__(self):  # pragma: nocover
        return (f"Comment #{self.pk} on artwork #{getattr(self.artwork, 'pk', None)}"
                f" by user #{getattr(self.user, 'pk', None)}")

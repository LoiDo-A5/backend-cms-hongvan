from django.db import models


class LikeCollection(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE, related_name='like_collections')
    collection = models.ForeignKey('artwork.Collection', on_delete=models.CASCADE, related_name='like_collections')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):  # pragma: nocover
        return f'{self.id}'

    class Meta:
        unique_together = ('user', 'collection')

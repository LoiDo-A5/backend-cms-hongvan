from django.db import models
import uuid


class Collection(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='collections')
    artworks = models.ManyToManyField('artwork.ArtWork', related_name='collections')
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    def __str__(self):  # pragma: nocover
        return self.title

    def has_owner(self, user):
        return user.id == self.owner_id

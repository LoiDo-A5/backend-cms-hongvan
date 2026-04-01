from django.db import models
import uuid
from django.utils import timezone

from artwork.models import ArtWork, Collection
from core.accounts.models import User

from common.abstract_models.image_field import CustomImageField


class ShareLink(models.Model):
    SHARE_TYPE_CHOICES = (
        ('artwork', 'Artwork'),
        ('collection', 'Collection'),
        ('exhibition', 'Exhibition'),
        ('mixed', 'Mixed'),
    )

    EXPIRATION_CHOICES = (
        ('never', 'Never'),
        ('custom', 'Custom'),
    )

    RECIPIENT_TYPE_CHOICES = (
        ('public', 'Public Link'),
        ('specific', 'Specific Users'),
        ('both', 'Both'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='share_links')
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    banner = CustomImageField(null=True, blank=True)

    share_type = models.CharField(max_length=20, choices=SHARE_TYPE_CHOICES, default='artwork')
    recipient_type = models.CharField(max_length=20, choices=RECIPIENT_TYPE_CHOICES, default='public')

    password = models.CharField(max_length=255, blank=True, null=True)
    expiration_type = models.CharField(max_length=20, choices=EXPIRATION_CHOICES, default='never')
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    access_count = models.IntegerField(default=0)
    last_accessed_at = models.DateTimeField(null=True, blank=True)

    is_share_all = models.BooleanField(default=False)
    shared_items = models.JSONField(default=list)
    artwork = models.ManyToManyField(ArtWork, related_name='share_links', blank=True)
    collections = models.ManyToManyField(Collection, related_name='collection_share_links', blank=True)
    recipients = models.ManyToManyField(User, related_name='received_share_links', blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Share Link {self.id} - {self.user.name} - {self.share_type}'

    @property
    def is_expired(self):
        if self.expiration_type == 'never' or not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return self.is_active and not self.is_expired

    def validate_password(self, provided_password):
        if not self.password:
            return True
        return self.password == provided_password

    def get_shared_artworks(self):
        if self.is_share_all:
            return ArtWork.objects.filter(owner=self.user)

        return self.artwork.all()

    def get_shared_collections(self):
        from artwork.models.collection import Collection

        if self.is_share_all:
            return Collection.objects.filter(owner=self.user)

        return self.collections.filter(owner=self.user)

    def get_shared_exhibitions(self):
        from artwork.models import Exhibition

        if self.is_share_all:
            return Exhibition.objects.filter(owner=self.user)

        return Exhibition.objects.none()

    def add_recipient(self, user):
        self.recipients.add(user)

    def get_share_url(self, request=None):
        if request:
            return f'{request.scheme}://{request.get_host()}/api/artwork/share/{self.id}/'
        return f'/api/artwork/share/{self.id}/'

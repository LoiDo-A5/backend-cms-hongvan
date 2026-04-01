import uuid
from django.db import models
from django.core.validators import MinValueValidator

from artwork.models.artwork_artist import ArtworkArtist
from artwork.utils.const import CATEGORY_CHOICES
from artwork.utils.const import STATUS_CHOICES
from artwork.models.color_artwork import ColorArtwork
from artwork.models.medium_artwork import MediumArtwork
from artwork.models.orientation_artwork import OrientationArtwork
from artwork.models.size_artwork import SizeArtwork
from artwork.models.style_artwork import StyleArtwork
from artwork.models.subject_artwork import SubjectArtwork
from common.abstract_models.image_field import CustomFileField
from core.accounts.models import User
from core.accounts.models.user_location import UserLocation
from common.abstract_models.active_model import ActiveModel
from common.abstract_models.active_model import ActiveManager
from django.db.models import F

CURRENCY_CHOICES = (
    ('vnd', 'VND'),
    ('usd', 'USD'),
)


class ArtworkManager(ActiveManager):
    def get_queryset(self):
        return (
            super().get_queryset()
            .exclude(status__in=['in_stock'])
        )


class ArtWork(ActiveModel):
    objects = ArtworkManager()

    uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='artworks_owner')
    artist_artwork = models.ForeignKey(ArtworkArtist, on_delete=models.SET_NULL, null=True,
                                       blank=True, related_name='artworks')
    artist = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='artworks_artist')
    artist_name = models.CharField(max_length=100, blank=True, null=True)
    contact_info_artist = models.CharField(max_length=100, blank=True, null=True)
    title = models.CharField(max_length=200, blank=True)
    description = models.CharField(max_length=10000, blank=True)
    note = models.CharField(max_length=500, blank=True)
    is_public = models.BooleanField(default=True)
    category = models.CharField(max_length=255, choices=CATEGORY_CHOICES, null=True)
    style = models.ForeignKey(StyleArtwork, on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.ForeignKey(SubjectArtwork, on_delete=models.SET_NULL, null=True, blank=True)
    subjects = models.ManyToManyField(SubjectArtwork, blank=True, related_name='artworks')
    color = models.ForeignKey(ColorArtwork, on_delete=models.SET_NULL, null=True, blank=True)
    medium = models.ForeignKey(MediumArtwork, on_delete=models.SET_NULL, null=True, blank=True)
    orientation = models.ForeignKey(OrientationArtwork, on_delete=models.SET_NULL, null=True, blank=True)
    size = models.ForeignKey(SizeArtwork, on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=255, choices=STATUS_CHOICES, default='', blank=True, null=True)
    currency = models.CharField(max_length=5, choices=CURRENCY_CHOICES, default='vnd', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_hide_price = models.BooleanField(default=False)
    is_ask_price_visible = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    year_created = models.IntegerField(null=True, blank=True)
    period_created = models.CharField(max_length=200, blank=True, null=True)
    total_edition = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    location = models.ForeignKey(UserLocation, on_delete=models.SET_NULL, null=True, blank=True)
    piece = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    linked_artwork = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='linked_artworks')
    is_public_certificate = models.BooleanField(default=False)
    show_comments = models.BooleanField(default=False)
    contact_information = models.CharField(max_length=255, blank=True, null=True)
    year_of_birth_artist = models.CharField(null=True, blank=True)
    inventory_code = models.CharField(max_length=200, blank=True, null=True)
    audio_file = CustomFileField(
        null=True,
        blank=True,
    )
    in_stock_date = models.DateField(null=True, blank=True)
    is_certificate_sync_disabled = models.BooleanField(
        default=False,
        help_text='When True, certificates will not be synced when artwork is updated. '
                  'This is set permanently once any certificate of the artwork has been transferred.',
    )

    def __str__(self):  # pragma: nocover
        return f'id:{self.id} | number:{self.title}'

    def delete(self, using=None, keep_parents=False, hard=False):
        if not self.has_certificate():
            hard = True
        super().delete(using=using, keep_parents=keep_parents, hard=hard)

    def has_owner(self, user):
        return user.id == self.owner_id

    def has_certificate(self):
        has_certificate_in_linked_artwork = False

        if self.linked_artwork:
            has_certificate_in_linked_artwork = self.linked_artwork.editions.filter(certificate__isnull=False).exists()

        has_certificate_in_self = self.editions.filter(certificate__isnull=False).exists()
        has_certificate_in_linked_artworks = (self.linked_artworks.filter(editions__certificate__isnull=False).exists())
        return has_certificate_in_self or has_certificate_in_linked_artwork or has_certificate_in_linked_artworks

    def has_transferred_certificate(self):
        from artwork.models.artwork_certificate import ArtworkCertificate

        has_transferred_in_self = ArtworkCertificate.objects.filter(
            artwork_edition__artwork=self,
        ).exclude(
            issued_by=F('issued_to'),
        ).exists()

        if has_transferred_in_self:
            return True

        if self.linked_artwork:
            has_transferred_in_linked = ArtworkCertificate.objects.filter(
                artwork_edition__artwork=self.linked_artwork,
            ).exclude(
                issued_by=F('issued_to'),
            ).exists()
            if has_transferred_in_linked:
                return True

        linked_artwork_ids = self.linked_artworks.values_list('id', flat=True)
        if linked_artwork_ids:
            has_transferred_in_linked_artworks = ArtworkCertificate.objects.filter(
                artwork_edition__artwork_id__in=linked_artwork_ids,
            ).exclude(
                issued_by=F('issued_to'),
            ).exists()
            if has_transferred_in_linked_artworks:
                return True

        return False

    def can_sync_certificates(self):
        if self.is_certificate_sync_disabled:
            return False
        return not self.has_transferred_certificate()

    def disable_certificate_sync(self):
        if not self.is_certificate_sync_disabled:
            self.is_certificate_sync_disabled = True
            self.save(update_fields=['is_certificate_sync_disabled'])

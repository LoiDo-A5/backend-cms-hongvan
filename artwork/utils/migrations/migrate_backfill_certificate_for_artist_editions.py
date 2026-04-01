from django.db import transaction
from django.db.models import Q

from core.accounts.models.user import USER_ROLE


def backfill_certificate_for_artist_editions(ArtWork, ArtworkEdition, ArtworkCertificate, OwnerCertificate):
    with transaction.atomic():
        artworks = ArtWork.objects.filter(owner__role=USER_ROLE.ARTIST)

        for artwork in artworks.iterator():
            artist = artwork.owner

            edition_qs = ArtworkEdition.objects.filter(artwork=artwork)
            eligible_editions = (
                edition_qs
                .filter(certificate__isnull=True)
                .filter(
                    Q(linked_edition__isnull=True)
                    | Q(linked_edition__certificate__isnull=True)
                )
                .filter(
                    Q(linked_edition_related__isnull=True)
                    | Q(linked_edition_related__certificate__isnull=True)
                )
            )

            for edition in eligible_editions.iterator():
                certificate = ArtworkCertificate.objects.create(
                    artwork_edition=edition,
                    issued_by=artist,
                    issued_to=artist,
                )
                OwnerCertificate.objects.create(
                    certificate=certificate,
                    user=artist,
                    name=getattr(artist, 'legal_name', None) or getattr(artist, 'name', None) or '',
                )

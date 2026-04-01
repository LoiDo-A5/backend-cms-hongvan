from django.db import transaction
from django.db.models import Q


USER_ROLE_ARTIST = 1


def backfill_certificates_for_artist_artworks(ArtWork, ArtworkEdition, ArtworkCertificate, OwnerCertificate):
    with transaction.atomic():
        artist_artworks = ArtWork.objects.filter(
            owner__role=USER_ROLE_ARTIST,
            owner__isnull=False,
            active=True,
        ).select_related('owner', 'location')

        for artwork in artist_artworks.iterator():
            artist = artwork.owner

            eligible_editions = (
                ArtworkEdition.objects.filter(artwork=artwork)
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

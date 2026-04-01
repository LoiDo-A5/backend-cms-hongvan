from django.db import transaction

from artwork.utils.const import STATUS_REQUEST
from core.accounts.models.user import USER_ROLE


def migrate_artist_tag_to_artist(ArtWork):
    with transaction.atomic():
        artworks = ArtWork.objects.select_related("owner").all()

        for artwork in artworks.iterator():
            owner = artwork.owner

            if owner is None:
                continue

            new_artist = None

            if owner.role == USER_ROLE.ARTIST:
                new_artist = owner
            elif owner.role in (USER_ROLE.GALLERY_OWNER, USER_ROLE.COLLECTOR):
                request = (
                    artwork.tag_request
                    .select_related('request_to')
                    .filter(
                        status__in=[
                            STATUS_REQUEST.REQUEST_RECEIVED,
                            STATUS_REQUEST.REQUEST_APPROVED,
                        ],
                    )
                    .order_by("id")
                    .first()
                )

                if request and request.request_to_id:
                    new_artist = request.request_to

            if new_artist is None or artwork.artist_id == getattr(new_artist, "id", None):
                continue

            artwork.artist = new_artist
            artwork.save(update_fields=["artist"])

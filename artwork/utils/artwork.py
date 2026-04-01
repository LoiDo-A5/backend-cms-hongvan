from artwork.models import ArtWork, StyleArtwork, SubjectArtwork, MediumArtwork, SizeArtwork, ImageArtwork, \
    ArtworkEdition
from artwork.serializers.artwork_copy import ArtworkCopySerializer, SizeArtworkCopySerializer

from artwork.serializers.edition_copy import EditionCopySerializer


def copy_artwork(sample_artwork, attribute_data=None):
    data = ArtworkCopySerializer(sample_artwork).data
    attribute_data = attribute_data or {}

    copy_artwork_attributes(sample_artwork=sample_artwork, attribute_data=attribute_data)
    artwork = ArtWork.objects.create(**data, **attribute_data)

    copy_artwork_images(sample_artwork=sample_artwork, artwork=artwork)

    return artwork


def copy_artwork_edition(sample_edition, attribute_data=None):
    data = EditionCopySerializer(sample_edition).data
    attribute_data = attribute_data or {}

    edition = ArtworkEdition.objects.create(**data, **attribute_data)
    return edition


def copy_artwork_attributes(sample_artwork, attribute_data):
    copy_attribute(sample_artwork=sample_artwork, attribute_data=attribute_data,
                   attribute_name='style', model=StyleArtwork)

    copy_attribute(sample_artwork=sample_artwork, attribute_data=attribute_data,
                   attribute_name='subject', model=SubjectArtwork)

    copy_attribute(sample_artwork=sample_artwork, attribute_data=attribute_data,
                   attribute_name='medium', model=MediumArtwork)

    copy_size_attribute(sample_artwork=sample_artwork, attribute_data=attribute_data)


def copy_attribute(sample_artwork, attribute_data, attribute_name, model):
    sample_attribute = getattr(sample_artwork, attribute_name, None)

    if not sample_attribute:
        return

    if not getattr(sample_attribute, 'user', None):
        attribute_data[attribute_name] = sample_attribute
        return

    instance, created = model.objects.get_or_create(
        name=sample_attribute.name,
        name_vi=sample_attribute.name_vi,
        category=sample_attribute.category,
        user=attribute_data.get('owner', None),
    )

    attribute_data[attribute_name] = instance


def copy_size_attribute(sample_artwork, attribute_data):
    sample_size = getattr(sample_artwork, 'size', None)

    if not sample_size:
        return

    data = SizeArtworkCopySerializer(sample_size).data

    attribute_data['size'] = SizeArtwork.objects.create(**data)


def copy_artwork_images(sample_artwork, artwork):
    sample_artwork_image = sample_artwork.imageartwork_set.all()

    new_images = [
        ImageArtwork(image=instance.image, artwork=artwork)
        for instance in sample_artwork_image
    ]

    ImageArtwork.objects.bulk_create(new_images)


def generate_artwork_edition(total_edition, artwork):
    new_editions = [
        ArtworkEdition(artwork=artwork, edition_number=num)
        for num in range(1, total_edition + 1)
    ]

    ArtworkEdition.objects.bulk_create(new_editions)


def get_artworks_by_role(user, is_owner):
    if is_owner:
        return ArtWork.objects.filter(owner_id=user.id)
    return None


def get_filtered_artworks(owner, artist_uuid, artist_artwork_id, is_owner):
    if artist_uuid:
        return filter_by_artist_uuid(artist_uuid, owner.uuid, is_owner)
    elif artist_artwork_id:
        return filter_by_artist_artwork_id(artist_artwork_id, is_owner)
    return ArtWork.objects.none()


def filter_by_artist_uuid(artist_uuid, owner_uuid, is_owner):
    base_filter = {
        'artist__uuid': artist_uuid,
        'owner__uuid': owner_uuid,
    }

    if is_owner:
        return ArtWork.objects.filter(**base_filter)
    else:
        return ArtWork.objects.filter(**base_filter, is_public=True)


def filter_by_artist_artwork_id(artist_artwork_id, is_owner):
    if is_owner:
        return ArtWork.objects.filter(artist_artwork_id=artist_artwork_id)
    else:
        return ArtWork.objects.filter(artist_artwork_id=artist_artwork_id, is_public=True)


def process_artists_data(official_artists, manual_artists, search_term, ordering):
    artists = (
        [
            {
                'id': artist['artist_id'],
                'uuid': artist['artist__uuid'],
                'artist_name': artist['artist__name'],
                'artwork_count': artist['artwork_count'],
                'year_of_birth': artist['artist__year_of_birth'],
            }
            for artist in official_artists
        ] + [
            {
                'id': artist['id'],
                'artist_name': artist['artist_name'],
                'year_of_birth': artist['year_of_birth'],
                'artwork_count': artist['artwork_count'],
            }
            for artist in manual_artists
        ]
    )

    if search_term:
        artists = [artist for artist in artists if search_term.lower() in artist['artist_name'].lower()]

    if ordering:
        if ordering == '-year_of_birth':
            artists = sorted(artists, key=lambda x: (x.get('year_of_birth')
                                                     is None, x.get('year_of_birth') or ''), reverse=True)
        elif ordering == 'alphabet':
            artists = sorted(artists, key=lambda x: x.get('artist_name', '').lower())
        elif ordering == '-alphabet':
            artists = sorted(artists, key=lambda x: x.get('artist_name', '').lower(), reverse=True)
        else:
            artists = sorted(artists, key=lambda x: (x.get('year_of_birth')
                                                     in [None, ''], x.get('year_of_birth') or ''))
    else:
        artists = sorted(artists, key=lambda x: (x.get('year_of_birth') in [None, ''], x.get('year_of_birth') or ''))

    return artists

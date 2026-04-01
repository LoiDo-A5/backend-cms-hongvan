from artwork.factories.artist_tag_request import ArtistTagRequestFactory
from artwork.factories.artwork import ArtworkFactory
from artwork.models import ArtWork
from artwork.models import ArtistTagRequest
from artwork.utils.const import STATUS_REQUEST
from artwork.utils.migrations.migrate_artist_tag_to_artist import migrate_artist_tag_to_artist
from common.tests.isolated_cache_test_case import TestCase
from core.accounts.factories.user import UserFactory
from core.accounts.models.user import USER_ROLE


class MigrateArtistTagToArtistTests(TestCase):
    def test_owner_is_artist_sets_artist_to_owner(self):
        owner = UserFactory(role=USER_ROLE.ARTIST)
        artwork = ArtworkFactory(owner=owner, artist=None)

        migrate_artist_tag_to_artist(ArtWork)

        artwork.refresh_from_db()
        self.assertEqual(artwork.artist, owner)

    def test_owner_is_gallery_owner_with_approved_request_sets_artist_from_request(self):
        owner = UserFactory(role=USER_ROLE.GALLERY_OWNER)
        artist = UserFactory(role=USER_ROLE.ARTIST)
        artwork = ArtworkFactory(owner=owner, artist=None)
        ArtistTagRequestFactory(
            artwork=artwork,
            request_by=owner,
            request_to=artist,
            status=STATUS_REQUEST.REQUEST_APPROVED,
        )

        migrate_artist_tag_to_artist(ArtWork)

        artwork.refresh_from_db()
        self.assertEqual(artwork.artist, artist)

    def test_owner_is_collector_with_received_request_sets_artist_from_request(self):
        owner = UserFactory()
        artist = UserFactory(role=USER_ROLE.ARTIST)
        artwork = ArtworkFactory(owner=owner, artist=None)
        ArtistTagRequestFactory(
            artwork=artwork,
            request_by=owner,
            request_to=artist,
            status=STATUS_REQUEST.REQUEST_RECEIVED,
        )

        migrate_artist_tag_to_artist(ArtWork)

        artwork.refresh_from_db()
        self.assertEqual(artwork.artist, artist)

    def test_owner_is_gallery_owner_without_request_keeps_artist_none(self):
        owner = UserFactory(role=USER_ROLE.GALLERY_OWNER)
        artwork = ArtworkFactory(owner=owner, artist=None)

        migrate_artist_tag_to_artist(ArtWork)

        artwork.refresh_from_db()
        self.assertIsNone(artwork.artist)

    def test_skip_denied_and_canceled_requests(self):
        owner = UserFactory()
        artist = UserFactory(role=USER_ROLE.ARTIST)
        artwork = ArtworkFactory(owner=owner, artist=None)

        ArtistTagRequestFactory(
            artwork=artwork,
            request_by=owner,
            request_to=artist,
            status=STATUS_REQUEST.REQUEST_DENIED,
        )
        ArtistTagRequestFactory(
            artwork=artwork,
            request_by=owner,
            request_to=artist,
            status=STATUS_REQUEST.REQUEST_CANCELED,
        )

        migrate_artist_tag_to_artist(ArtWork)

        artwork.refresh_from_db()
        self.assertIsNone(artwork.artist)

    def test_skip_artwork_missing_owner(self):
        artwork = ArtworkFactory(owner=None, artist=None)

        migrate_artist_tag_to_artist(ArtWork)

        artwork.refresh_from_db()
        self.assertIsNone(artwork.artist)

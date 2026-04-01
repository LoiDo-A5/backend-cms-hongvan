from artwork.factories.artwork import ArtworkFactory
from artwork.models import ArtWork
from artwork.utils.migrations.migrate_update_owner_field_artwork import update_owner_field_artwork
from common.tests.isolated_cache_test_case import TestCase
from core.accounts.factories.user import UserFactory


class MigrateUpdateOwnerFieldArtworkTests(TestCase):
    def test_update_owner_field_artwork(self):
        artist = UserFactory()
        owner = UserFactory()
        artworks_with_no_owner = ArtworkFactory.create_batch(3, artist=artist, owner=None)
        artworks_with_owner = ArtworkFactory.create_batch(2, artist=artist, owner=owner)

        update_owner_field_artwork(ArtWork)

        for artwork in artworks_with_no_owner:
            artwork.refresh_from_db()
            self.assertEqual(artwork.owner, artist)

        for artwork in artworks_with_owner:
            artwork.refresh_from_db()
            self.assertNotEqual(artwork.owner, artist)

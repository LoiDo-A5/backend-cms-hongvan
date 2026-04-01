from artwork.factories.artwork import ArtworkFactory
from artwork.factories.artwork_edition import ArtworkEditionFactory
from artwork.models import ArtworkEdition
from artwork.utils.migrations.migrate_update_status_and_location_editions_artwork import \
    update_status_and_location_editions_artwork
from common.tests.isolated_cache_test_case import TestCase


class MigrateUpdateStatusAndLocationArtworkEditionTests(TestCase):
    def test_migrate_update_status_and_location_editions_artwork(self):
        artwork = ArtworkFactory(total_edition=5)
        artwork_edition1 = ArtworkEditionFactory(artwork=artwork, status=None, location=None)
        artwork_edition2 = ArtworkEditionFactory(artwork=artwork, status=None, location=None)

        update_status_and_location_editions_artwork(ArtworkEdition)
        artwork_edition1.refresh_from_db()
        artwork_edition2.refresh_from_db()
        self.assertEqual(artwork_edition1.status, artwork.status)
        self.assertEqual(artwork_edition1.location, artwork.location)
        self.assertEqual(artwork_edition2.status, artwork.status)
        self.assertEqual(artwork_edition2.location, artwork.location)


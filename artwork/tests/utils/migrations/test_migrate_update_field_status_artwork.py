from common.tests.isolated_cache_test_case import TestCase
from artwork.factories.artwork import ArtworkFactory
from artwork.utils.migrations.migrate_update_field_status import update_field_status
from artwork.models.artwork import ArtWork


class MigrateUpdateUpdateStatusArtworkTests(TestCase):
    def test_migrate_update_field_status(self):
        artwork = ArtworkFactory(status='abc')
        artwork_2 = ArtworkFactory(status='bcd')
        artwork_3 = ArtworkFactory(status='available')
        artwork_4 = ArtworkFactory(status='not_for_sale')

        update_field_status(ArtWork)

        artwork.refresh_from_db()
        artwork_2.refresh_from_db()
        artwork_3.refresh_from_db()
        artwork_4.refresh_from_db()

        self.assertEqual(artwork.status, '')
        self.assertEqual(artwork_2.status, '')
        self.assertEqual(artwork_3.status, 'available')
        self.assertEqual(artwork_4.status, 'not_for_sale')

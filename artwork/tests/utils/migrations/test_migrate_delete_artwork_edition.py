from artwork.utils.migrations.migrate_remove_editions_artwork import remove_editions_artwork
from artwork.utils.migrations.migrate_remove_editions_artwork import update_artwork_total_edition
from common.tests.isolated_cache_test_case import TestCase
from artwork.models.artwork import ArtWork
from artwork.models.artwork_edition import ArtworkEdition
from artwork.factories.artwork import ArtworkFactory
from artwork.factories.artwork_edition import ArtworkEditionFactory


class MigrateDeleteArtworkEditionTests(TestCase):
    def test_migrate_delete_editions_artwork(self):
        artwork = ArtworkFactory(total_edition=100)

        for x in range(100):
            ArtworkEditionFactory(artwork=artwork, edition_number=x+1)

        editions = ArtworkEdition.objects.count()
        self.assertEqual(editions, 100)

        remove_editions_artwork(ArtworkEdition)
        editions = ArtworkEdition.objects.count()
        self.assertEqual(editions, 20)

    def test_migrate_update_artwork_total_edition(self):
        artwork = ArtworkFactory(total_edition=100)
        artwork_2 = ArtworkFactory(total_edition=20)
        artwork_3 = ArtworkFactory(total_edition=10)

        update_artwork_total_edition(ArtWork)

        artwork.refresh_from_db()
        artwork_2.refresh_from_db()
        artwork_3.refresh_from_db()

        self.assertEqual(artwork.total_edition, 20)
        self.assertEqual(artwork_2.total_edition, 20)
        self.assertEqual(artwork_3.total_edition, 10)


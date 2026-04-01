from artwork.utils.migrations.migrate_create_editions_artwork import create_editions_artwork
from common.tests.isolated_cache_test_case import TestCase
from artwork.models.artwork import ArtWork
from artwork.models.artwork_edition import ArtworkEdition
from artwork.factories.artwork import ArtworkFactory
from artwork.factories.artwork_edition import ArtworkEditionFactory


class MigrateCreateArtworkEditionTests(TestCase):
    def test_migrate_create_editions_artwork(self):
        artwork = ArtworkFactory(total_edition=4)

        editions = ArtworkEdition.objects.all()
        self.assertEqual(len(editions), 0)

        create_editions_artwork(ArtWork, ArtworkEdition)

        editions = ArtworkEdition.objects.all()
        self.assertEqual(len(editions), 4)
        self.assertEqual(editions[0].artwork, artwork)

    def test_migrate_create_editions_artwork_when_artwork_already_has_editions(self):
        artwork = ArtworkFactory(total_edition=5)
        ArtworkEditionFactory(artwork=artwork)
        ArtworkEditionFactory(artwork=artwork)

        editions = ArtworkEdition.objects.all()
        self.assertEqual(len(editions), 2)

        create_editions_artwork(ArtWork, ArtworkEdition)

        editions = ArtworkEdition.objects.all()
        self.assertEqual(len(editions), 5)

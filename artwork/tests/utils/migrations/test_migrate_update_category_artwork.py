from artwork.factories.artwork import ArtworkFactory
from artwork.factories.color_artwork import ColorArtworkFactory
from artwork.factories.medium_artwork import MediumArtworkFactory
from artwork.factories.orientation_artwork import OrientationArtworkFactory
from artwork.factories.size_artwork import SizeArtworkFactory
from artwork.factories.style_artwork import StyleArtworkFactory
from artwork.factories.subject_artwork import SubjectArtworkFactory
from artwork.models import ArtWork
from artwork.models import ColorArtwork
from artwork.models import MediumArtwork
from artwork.models import OrientationArtwork
from artwork.models import SizeArtwork
from artwork.models import StyleArtwork
from artwork.models import SubjectArtwork
from artwork.utils.migrations.migrate_update_category_artwork import update_category_artwork
from common.tests.isolated_cache_test_case import TestCase


class MigrateUpdateCategoryArtworkTests(TestCase):
    def refresh_and_assert_category(self, instance, expected_category='painting'):
        instance.refresh_from_db()
        self.assertEqual(instance.category, expected_category)

    def test_migrate_update_category_artwork(self):
        artwork = ArtworkFactory()
        artwork2 = ArtworkFactory(category='sculpture')
        colorArtwork = ColorArtworkFactory()
        colorArtwork2 = ColorArtworkFactory(category='sculpture')
        mediumArtwork = MediumArtworkFactory()
        mediumArtwork2 = MediumArtworkFactory(category='sculpture')
        orientationArtwork = OrientationArtworkFactory()
        orientationArtwork2 = OrientationArtworkFactory(category='sculpture')
        sizeArtwork = SizeArtworkFactory()
        sizeArtwork2 = SizeArtworkFactory(category='sculpture')
        styleArtwork = StyleArtworkFactory()
        styleArtwork2 = StyleArtworkFactory(category='sculpture')
        subjectArtwork = SubjectArtworkFactory()
        subjectArtwork2 = SubjectArtworkFactory(category='sculpture')

        update_category_artwork(ArtWork, ColorArtwork, MediumArtwork, OrientationArtwork, SizeArtwork, StyleArtwork,
                                SubjectArtwork)

        self.refresh_and_assert_category(artwork)
        self.refresh_and_assert_category(artwork2)
        self.refresh_and_assert_category(colorArtwork)
        self.refresh_and_assert_category(colorArtwork2)
        self.refresh_and_assert_category(mediumArtwork)
        self.refresh_and_assert_category(mediumArtwork2)
        self.refresh_and_assert_category(orientationArtwork)
        self.refresh_and_assert_category(orientationArtwork2)
        self.refresh_and_assert_category(sizeArtwork)
        self.refresh_and_assert_category(sizeArtwork2)
        self.refresh_and_assert_category(styleArtwork)
        self.refresh_and_assert_category(styleArtwork2)
        self.refresh_and_assert_category(subjectArtwork)
        self.refresh_and_assert_category(subjectArtwork2)

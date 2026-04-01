from artwork.factories.artwork import ArtworkFactory
from artwork.models import ArtWork
from artwork.utils.migrations.migrate_subject_to_subjects import update_subject_to_subjects
from common.tests.isolated_cache_test_case import TestCase


class MigrateUpdateSubjectToSubjectsArtwork(TestCase):
    def test_migrate_subject_to_subjects(self):

        artwork = ArtworkFactory(subject=None)
        artwork1 = ArtworkFactory()
        artwork2 = ArtworkFactory()

        self.assertEqual(artwork.subjects.count(), 0)
        self.assertEqual(artwork1.subjects.count(), 0)
        self.assertEqual(artwork1.subjects.count(), 0)

        update_subject_to_subjects(ArtWork)

        artwork.refresh_from_db()
        artwork1.refresh_from_db()
        artwork2.refresh_from_db()

        self.assertEqual(artwork.subjects.count(), 0)

        self.assertEqual(artwork1.subjects.count(), 1)
        self.assertIn(artwork1.subject, artwork1.subjects.all())

        self.assertEqual(artwork2.subjects.count(), 1)
        self.assertIn(artwork2.subject, artwork2.subjects.all())

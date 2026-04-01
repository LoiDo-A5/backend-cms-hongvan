from artwork.utils.migrations.migrate_update_field_issued_by_certificate import update_field_issued_by
from common.tests.isolated_cache_test_case import TestCase
from artwork.factories.artwork_certificate import ArtworkCertificateFactory
from artwork.models.artwork_certificate import ArtworkCertificate


class MigrateUpdateCertificateFieldIssueByTests(TestCase):
    def test_migrate_update_field_issued_by(self):

        certificate = ArtworkCertificateFactory(issued_by=None)
        artist = certificate.artwork_edition.artwork.artist
        update_field_issued_by(ArtworkCertificate)

        certificate.refresh_from_db()

        self.assertEqual(certificate.issued_by, artist)
        self.assertEqual(certificate.issued_to, artist)

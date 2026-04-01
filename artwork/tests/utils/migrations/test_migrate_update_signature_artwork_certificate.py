from artwork.factories.artwork import ArtworkFactory
from artwork.factories.artwork_certificate import ArtworkCertificateFactory
from artwork.factories.artwork_edition import ArtworkEditionFactory
from artwork.models import ArtworkCertificate
from artwork.utils.migrations.migrate_update_signature_artwork_certificate import update_signature_artwork_certificate
from common.tests.isolated_cache_test_case import TestCase
from core.accounts.factories.user import UserProfileFactory, UserFactory
from core.accounts.models import UserProfile


class MigrateUpdateSignatureArtworkCertificateTests(TestCase):
    def test_migrate_update_signature_artwork_certificate(self):
        user = UserFactory()
        user_profile = UserProfileFactory(user=user, signature='image1.png')

        artwork_edition_1 = ArtworkEditionFactory(artwork__artist=user)
        artwork_edition_2 = ArtworkEditionFactory(artwork__artist=user)
        artwork_edition_3 = ArtworkEditionFactory(artwork__artist=user)

        artwork_certificate1 = ArtworkCertificateFactory(artwork_edition=artwork_edition_1, signature=None)
        artwork_certificate2 = ArtworkCertificateFactory(artwork_edition=artwork_edition_2, signature=None)
        artwork_certificate3 = ArtworkCertificateFactory(artwork_edition=artwork_edition_3)

        update_signature_artwork_certificate(ArtworkCertificate, UserProfile)

        artwork_certificate1.refresh_from_db()
        artwork_certificate2.refresh_from_db()
        artwork_certificate3.refresh_from_db()

        self.assertEqual(artwork_certificate1.signature, user_profile.signature)
        self.assertEqual(artwork_certificate2.signature, user_profile.signature)

        self.assertIsNotNone(artwork_certificate3.signature)
        self.assertNotEqual(artwork_certificate3.signature, user_profile.signature)

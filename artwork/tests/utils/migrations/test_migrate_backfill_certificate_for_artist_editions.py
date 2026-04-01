from artwork.factories.artwork import ArtworkFactory
from artwork.factories.artwork_certificate import ArtworkCertificateFactory
from artwork.factories.artwork_edition import ArtworkEditionFactory
from artwork.models import ArtWork
from artwork.models import ArtworkCertificate
from artwork.models import ArtworkEdition
from artwork.models import OwnerCertificate
from artwork.utils.migrations.migrate_backfill_certificate_for_artist_editions import (
    backfill_certificate_for_artist_editions,
)
from common.tests.isolated_cache_test_case import TestCase
from core.accounts.factories.user import UserFactory
from core.accounts.models import User
from core.accounts.models.user import USER_ROLE


class BackfillCertificateForArtistEditionsTests(TestCase):
    def run_backfill(self):
        backfill_certificate_for_artist_editions(
            ArtWork,
            ArtworkEdition,
            ArtworkCertificate,
            OwnerCertificate,
        )

    def test_artist_without_artworks_does_nothing(self):
        UserFactory(role=USER_ROLE.ARTIST)

        self.run_backfill()

        self.assertEqual(ArtworkCertificate.objects.count(), 0)
        self.assertEqual(OwnerCertificate.objects.count(), 0)

    def test_artist_with_editions_without_any_certificate_creates_certificate_and_owner_certificate(self):
        artist = UserFactory(role=USER_ROLE.ARTIST, legal_name='Artist Legal')

        artwork_1 = ArtworkFactory(owner=artist)
        artwork_2 = ArtworkFactory(owner=artist)

        editions = [
            ArtworkEditionFactory(artwork=artwork_1, edition_number=1),
            ArtworkEditionFactory(artwork=artwork_1, edition_number=2),
            ArtworkEditionFactory(artwork=artwork_2, edition_number=1),
        ]

        self.run_backfill()

        self.assertEqual(ArtworkCertificate.objects.count(), len(editions))
        self.assertEqual(OwnerCertificate.objects.count(), len(editions))

        for edition in editions:
            edition.refresh_from_db()
            certificate = getattr(edition, 'certificate', None)
            self.assertIsNotNone(certificate)
            self.assertEqual(certificate.issued_by, artist)
            self.assertEqual(certificate.issued_to, artist)
            self.assertEqual(certificate.owner.user, artist)
            self.assertEqual(certificate.owner.name, 'Artist Legal')

    def test_artist_with_existing_certificate_skips_creating_any_new_certificates(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)
        artwork = ArtworkFactory(owner=artist)

        edition_1 = ArtworkEditionFactory(artwork=artwork, edition_number=1)
        edition_2 = ArtworkEditionFactory(artwork=artwork, edition_number=2)

        ArtworkCertificateFactory(artwork_edition=edition_1)

        self.run_backfill()

        self.assertEqual(ArtworkCertificate.objects.count(), 2)
        edition_2.refresh_from_db()
        self.assertTrue(hasattr(edition_2, 'certificate'))

    def test_artist_with_linked_edition_certificate_skips(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)
        artwork = ArtworkFactory(owner=artist)

        base = ArtworkEditionFactory(artwork=artwork, edition_number=1)
        linked = ArtworkEditionFactory(artwork=artwork, edition_number=2, linked_edition=base)

        ArtworkCertificateFactory(artwork_edition=base)

        self.run_backfill()

        self.assertEqual(ArtworkCertificate.objects.count(), 1)
        linked.refresh_from_db()
        self.assertFalse(hasattr(linked, 'certificate'))

    def test_artist_with_reverse_linked_edition_certificate_skips(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)
        artwork = ArtworkFactory(owner=artist)

        base = ArtworkEditionFactory(artwork=artwork, edition_number=1)
        linked = ArtworkEditionFactory(artwork=artwork, edition_number=2, linked_edition=base)

        ArtworkCertificateFactory(artwork_edition=linked)

        self.run_backfill()

        self.assertEqual(ArtworkCertificate.objects.count(), 1)
        base.refresh_from_db()
        self.assertFalse(hasattr(base, 'certificate'))

    def test_linked_editions_without_certificates_creates_for_both(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)
        artwork = ArtworkFactory(owner=artist)

        base = ArtworkEditionFactory(artwork=artwork, edition_number=1)
        linked = ArtworkEditionFactory(artwork=artwork, edition_number=2, linked_edition=base)

        self.run_backfill()

        self.assertEqual(ArtworkCertificate.objects.count(), 2)
        base.refresh_from_db()
        linked.refresh_from_db()
        self.assertTrue(hasattr(base, 'certificate'))
        self.assertTrue(hasattr(linked, 'certificate'))

    def test_non_artist_owner_is_not_processed(self):
        collector = UserFactory(role=USER_ROLE.COLLECTOR)
        artwork = ArtworkFactory(owner=collector)
        ArtworkEditionFactory.create_batch(2, artwork=artwork)

        self.run_backfill()

        self.assertEqual(ArtworkCertificate.objects.count(), 0)
        self.assertEqual(OwnerCertificate.objects.count(), 0)

    def test_idempotent_running_twice_does_not_duplicate(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)
        artwork = ArtworkFactory(owner=artist)
        editions = ArtworkEditionFactory.create_batch(3, artwork=artwork)

        self.run_backfill()
        self.run_backfill()

        self.assertEqual(ArtworkCertificate.objects.count(), len(editions))
        self.assertEqual(OwnerCertificate.objects.count(), len(editions))

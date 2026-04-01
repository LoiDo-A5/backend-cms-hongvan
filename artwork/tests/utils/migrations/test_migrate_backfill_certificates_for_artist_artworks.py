from artwork.factories.artwork import ArtworkFactory
from artwork.factories.artwork_certificate import ArtworkCertificateFactory
from artwork.factories.artwork_edition import ArtworkEditionFactory
from artwork.models import ArtWork
from artwork.models import ArtworkCertificate
from artwork.models import ArtworkEdition
from artwork.models import OwnerCertificate
from artwork.utils.migrations.migrate_backfill_certificates_for_artist_artworks import (
    backfill_certificates_for_artist_artworks,
)
from common.tests.isolated_cache_test_case import TestCase
from core.accounts.factories.user import UserFactory
from core.accounts.models.user import USER_ROLE


class BackfillCertificatesForArtistArtworksTests(TestCase):
    def run_backfill(self):
        backfill_certificates_for_artist_artworks(
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

        artwork_1 = ArtworkFactory(owner=artist, active=True)
        artwork_2 = ArtworkFactory(owner=artist, active=True)

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

    def test_artist_with_existing_certificate_skips_creating_new_certificate(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)
        artwork = ArtworkFactory(owner=artist, active=True)

        edition_1 = ArtworkEditionFactory(artwork=artwork, edition_number=1)
        edition_2 = ArtworkEditionFactory(artwork=artwork, edition_number=2)

        ArtworkCertificateFactory(artwork_edition=edition_1)

        self.assertEqual(ArtworkCertificate.objects.count(), 1)
        self.run_backfill()

        self.assertEqual(ArtworkCertificate.objects.count(), 2)
        edition_2.refresh_from_db()
        self.assertTrue(hasattr(edition_2, 'certificate'))

    def test_artist_with_linked_edition_certificate_skips(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)
        artwork = ArtworkFactory(owner=artist, active=True)

        base = ArtworkEditionFactory(artwork=artwork, edition_number=1)
        linked = ArtworkEditionFactory(artwork=artwork, edition_number=2, linked_edition=base)

        ArtworkCertificateFactory(artwork_edition=base)

        self.run_backfill()

        self.assertEqual(ArtworkCertificate.objects.count(), 1)
        linked.refresh_from_db()
        self.assertFalse(hasattr(linked, 'certificate'))

    def test_artist_with_reverse_linked_edition_certificate_skips(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)
        artwork = ArtworkFactory(owner=artist, active=True)

        base = ArtworkEditionFactory(artwork=artwork, edition_number=1)
        linked = ArtworkEditionFactory(artwork=artwork, edition_number=2, linked_edition=base)

        ArtworkCertificateFactory(artwork_edition=linked)

        self.run_backfill()

        self.assertEqual(ArtworkCertificate.objects.count(), 1)
        base.refresh_from_db()
        self.assertFalse(hasattr(base, 'certificate'))

    def test_linked_editions_without_certificates_creates_for_both(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)
        artwork = ArtworkFactory(owner=artist, active=True)

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
        artwork = ArtworkFactory(owner=collector, active=True)
        ArtworkEditionFactory.create_batch(2, artwork=artwork)

        self.run_backfill()

        self.assertEqual(ArtworkCertificate.objects.count(), 0)
        self.assertEqual(OwnerCertificate.objects.count(), 0)

    def test_inactive_artwork_is_not_processed(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)
        artwork = ArtworkFactory(owner=artist, active=False)
        ArtworkEditionFactory.create_batch(2, artwork=artwork)

        self.run_backfill()

        self.assertEqual(ArtworkCertificate.objects.count(), 0)
        self.assertEqual(OwnerCertificate.objects.count(), 0)

    def test_artwork_without_owner_is_not_processed(self):
        artwork = ArtworkFactory(owner=None, active=True)
        ArtworkEditionFactory.create_batch(2, artwork=artwork)

        self.run_backfill()

        self.assertEqual(ArtworkCertificate.objects.count(), 0)
        self.assertEqual(OwnerCertificate.objects.count(), 0)

    def test_idempotent_running_twice_does_not_duplicate(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)
        artwork = ArtworkFactory(owner=artist, active=True)
        editions = ArtworkEditionFactory.create_batch(3, artwork=artwork)

        self.run_backfill()
        self.run_backfill()

        self.assertEqual(ArtworkCertificate.objects.count(), len(editions))
        self.assertEqual(OwnerCertificate.objects.count(), len(editions))

    def test_uses_name_when_legal_name_is_none(self):
        artist = UserFactory(role=USER_ROLE.ARTIST, legal_name=None, name='Artist Name')
        artwork = ArtworkFactory(owner=artist, active=True)
        edition = ArtworkEditionFactory(artwork=artwork, edition_number=1)

        self.run_backfill()

        edition.refresh_from_db()
        certificate = edition.certificate
        self.assertEqual(certificate.owner.name, 'Artist Name')

    def test_uses_empty_string_when_legal_name_and_name_are_none(self):
        artist = UserFactory(role=USER_ROLE.ARTIST, legal_name=None, name=None)
        artwork = ArtworkFactory(owner=artist, active=True)
        edition = ArtworkEditionFactory(artwork=artwork, edition_number=1)

        self.run_backfill()

        edition.refresh_from_db()
        certificate = edition.certificate
        self.assertEqual(certificate.owner.name, '')

    def test_certificates_equal_to_edition_volume(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)
        artwork = ArtworkFactory(owner=artist, active=True)
        edition_volume = 5
        editions = ArtworkEditionFactory.create_batch(edition_volume, artwork=artwork)

        self.run_backfill()

        self.assertEqual(ArtworkCertificate.objects.count(), edition_volume)
        self.assertEqual(OwnerCertificate.objects.count(), edition_volume)

        for edition in editions:
            edition.refresh_from_db()
            self.assertTrue(hasattr(edition, 'certificate'))

    def test_multiple_artists_with_multiple_artworks(self):
        artist_1 = UserFactory(role=USER_ROLE.ARTIST)
        artist_2 = UserFactory(role=USER_ROLE.ARTIST)

        artwork_1 = ArtworkFactory(owner=artist_1, active=True)
        artwork_2 = ArtworkFactory(owner=artist_2, active=True)

        ArtworkEditionFactory.create_batch(2, artwork=artwork_1)
        ArtworkEditionFactory.create_batch(3, artwork=artwork_2)

        self.run_backfill()

        self.assertEqual(ArtworkCertificate.objects.count(), 5)
        self.assertEqual(OwnerCertificate.objects.count(), 5)

        artwork_1_certs = ArtworkCertificate.objects.filter(
            artwork_edition__artwork=artwork_1
        )
        artwork_2_certs = ArtworkCertificate.objects.filter(
            artwork_edition__artwork=artwork_2
        )

        self.assertEqual(artwork_1_certs.count(), 2)
        self.assertEqual(artwork_2_certs.count(), 3)

        for cert in artwork_1_certs:
            self.assertEqual(cert.issued_by, artist_1)
            self.assertEqual(cert.issued_to, artist_1)

        for cert in artwork_2_certs:
            self.assertEqual(cert.issued_by, artist_2)
            self.assertEqual(cert.issued_to, artist_2)

    def test_gallery_owner_is_not_processed(self):
        gallery_owner = UserFactory(role=USER_ROLE.GALLERY_OWNER)
        artwork = ArtworkFactory(owner=gallery_owner, active=True)
        ArtworkEditionFactory.create_batch(2, artwork=artwork)

        self.run_backfill()

        self.assertEqual(ArtworkCertificate.objects.count(), 0)
        self.assertEqual(OwnerCertificate.objects.count(), 0)

    def test_service_provider_is_not_processed(self):
        service_provider = UserFactory(role=USER_ROLE.SERVICE_PROVIDER)
        artwork = ArtworkFactory(owner=service_provider, active=True)
        ArtworkEditionFactory.create_batch(2, artwork=artwork)

        self.run_backfill()

        self.assertEqual(ArtworkCertificate.objects.count(), 0)
        self.assertEqual(OwnerCertificate.objects.count(), 0)

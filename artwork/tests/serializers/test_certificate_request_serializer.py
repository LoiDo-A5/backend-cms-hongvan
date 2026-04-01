from types import SimpleNamespace

from artwork.factories.artwork import ArtworkFactory
from artwork.factories.artwork_edition import ArtworkEditionFactory
from core.accounts.tests.api.base_user_test import BaseUserTest
from artwork.serializers.certificate_request import ApproveCertificateRequestSerializer


class CertificateRequestSerializerInternalsTest(BaseUserTest):
    def get_serializer(self):
        ctx = {'request': SimpleNamespace(user=self.user)}
        return ApproveCertificateRequestSerializer(context=ctx)

    def test_update_edition_and_artwork_status_sets_user_and_marks_sold(self):
        artwork = ArtworkFactory(owner=self.user, status='available')
        edition = ArtworkEditionFactory(artwork=artwork, status='available')
        serializer = self.get_serializer()
        serializer.update_edition_and_artwork_status(edition, user=self.user)
        edition.refresh_from_db()
        artwork.refresh_from_db()
        self.assertEqual(edition.status, 'available')
        self.assertEqual(artwork.status, 'available')
        self.assertIsNotNone(getattr(artwork, '_current_user'))
        self.assertEqual(getattr(artwork, '_current_user'), self.user)

    def test_update_edition_and_artwork_status_without_user_does_not_set_current_user(self):
        artwork = ArtworkFactory(owner=self.user, status='available')
        edition = ArtworkEditionFactory(artwork=artwork, status='available')
        serializer = self.get_serializer()
        serializer.update_edition_and_artwork_status(edition, user=None)
        edition.refresh_from_db()
        artwork.refresh_from_db()
        self.assertEqual(edition.status, 'available')
        self.assertEqual(artwork.status, 'available')
        self.assertIsNone(getattr(artwork, '_current_user', None))

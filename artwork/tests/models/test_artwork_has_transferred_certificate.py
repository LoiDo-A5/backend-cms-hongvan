from artwork.factories.artwork import ArtworkFactory
from artwork.factories.artwork_edition import ArtworkEditionFactory
from artwork.factories.artwork_certificate import ArtworkCertificateFactory
from core.accounts.factories.user import UserFactory
from core.accounts.models.user import USER_ROLE
from core.accounts.tests.api.base_user_test import BaseUserTest


class ArtworkTransferredCertificateFlagsTests(BaseUserTest):
    def test_has_transferred_certificate_true_on_linked_artworks(self):
        base_owner = UserFactory(role=USER_ROLE.COLLECTOR)
        parent = ArtworkFactory(owner=base_owner)
        child = ArtworkFactory(linked_artwork=parent)
        edition = ArtworkEditionFactory(artwork=child)

        artist = UserFactory(role=USER_ROLE.ARTIST)
        recipient = UserFactory(role=USER_ROLE.COLLECTOR)
        ArtworkCertificateFactory(artwork_edition=edition, issued_by=artist, issued_to=recipient)

        self.assertTrue(parent.has_transferred_certificate())

    def test_has_transferred_certificate_false_and_can_sync_certificates_true(self):
        owner = UserFactory(role=USER_ROLE.COLLECTOR)
        artwork = ArtworkFactory(owner=owner)

        self.assertFalse(artwork.has_transferred_certificate())
        self.assertTrue(artwork.can_sync_certificates())

    def test_can_sync_certificates_false_when_sync_disabled(self):
        owner = UserFactory(role=USER_ROLE.COLLECTOR)
        artwork = ArtworkFactory(owner=owner)
        artwork.is_certificate_sync_disabled = True
        artwork.save(update_fields=['is_certificate_sync_disabled'])

        self.assertFalse(artwork.can_sync_certificates())

    def test_has_transferred_certificate_false_with_linked_artworks_without_transfer(self):
        base_owner = UserFactory(role=USER_ROLE.COLLECTOR)
        parent = ArtworkFactory(owner=base_owner)
        child = ArtworkFactory(linked_artwork=parent)
        edition = ArtworkEditionFactory(artwork=child)

        artist = UserFactory(role=USER_ROLE.ARTIST)
        recipient = artist
        ArtworkCertificateFactory(artwork_edition=edition, issued_by=artist, issued_to=recipient)

        self.assertFalse(parent.has_transferred_certificate())

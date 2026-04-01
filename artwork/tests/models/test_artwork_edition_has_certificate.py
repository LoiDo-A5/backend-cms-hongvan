from core.accounts.tests.api.base_user_test import BaseUserTest
from artwork.factories.artwork import ArtworkFactory
from artwork.factories.artwork_edition import ArtworkEditionFactory
from artwork.factories.artwork_certificate import ArtworkCertificateFactory


class ArtworkEditionHasCertificateTest(BaseUserTest):
    def test_has_certificate_true_when_linked_edition_has_certificate(self):
        base_artwork = ArtworkFactory()
        a = ArtworkEditionFactory(artwork=base_artwork, edition_number=1)
        b = ArtworkEditionFactory(artwork=base_artwork, edition_number=2)
        a.linked_edition = b
        a.save()
        ArtworkCertificateFactory(artwork_edition=b)
        self.assertTrue(a.has_certificate())

    def test_has_certificate_true_when_reverse_linked_edition_has_certificate(self):
        base_artwork = ArtworkFactory()
        a = ArtworkEditionFactory(artwork=base_artwork, edition_number=1)
        c = ArtworkEditionFactory(artwork=base_artwork, edition_number=3)
        c.linked_edition = a
        c.save()
        ArtworkCertificateFactory(artwork_edition=c)
        self.assertTrue(a.has_certificate())

    def test_has_certificate_false_when_no_certificate_anywhere(self):
        base_artwork = ArtworkFactory()
        d = ArtworkEditionFactory(artwork=base_artwork, edition_number=4)
        self.assertFalse(d.has_certificate())

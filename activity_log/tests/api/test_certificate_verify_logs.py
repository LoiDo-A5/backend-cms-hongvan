from rest_framework import status

from activity_log.factories.certificate_log import CertificateLogFactory
from artwork.factories.artwork import ArtworkFactory
from artwork.factories.artwork_certificate import ArtworkCertificateFactory
from artwork.factories.artwork_edition import ArtworkEditionFactory
from artwork.utils.const import VERIFY
from core.accounts.tests.api.base_user_test import BaseUserTest


class CertificateVerifyLogApiTests(BaseUserTest):
    def setUp(self) -> None:
        super().setUp()
        self.artwork1 = ArtworkFactory(artist=self.user, title='artwork')
        edition_1 = ArtworkEditionFactory(artwork=self.artwork1)

        self.certificate_1 = ArtworkCertificateFactory(artwork_edition=edition_1)
        self.certificate_log_1 = CertificateLogFactory(
            certificate=self.certificate_1,
            user=self.user,
            action_type=VERIFY,
        )
        self.certificate_log_2 = CertificateLogFactory(
            certificate=self.certificate_1,
            user=self.user,
            action_type=VERIFY,
        )

    def test_get_certificate_verify_logs_by_certificate_id(self):
        response = self.client.get('/api/activity_log/certificate_verify_logs/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

from rest_framework import status

from activity_log.factories.certificate_log import CertificateLogFactory
from artwork.factories.artwork import ArtworkFactory
from artwork.factories.artwork_certificate import ArtworkCertificateFactory
from artwork.factories.artwork_edition import ArtworkEditionFactory
from core.accounts.tests.api.base_user_test import BaseUserTest


class CertificateExportLogApiTests(BaseUserTest):
    def setUp(self) -> None:
        super().setUp()
        artwork1 = ArtworkFactory(artist=self.user)
        edition_1 = ArtworkEditionFactory(artwork=artwork1)

        self.certificate_1 = ArtworkCertificateFactory(artwork_edition=edition_1)
        self.certificate_log_1 = CertificateLogFactory(certificate=self.certificate_1)
        self.certificate_log_2 = CertificateLogFactory(certificate=self.certificate_1)

    def test_get_certificate_logs_by_certificate_id(self):
        response = self.client.get('/api/activity_log/certificate_export_logs/', {
            'certificate_id': self.certificate_1.id,
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['certificate'], self.certificate_1.id)
        self.assertEqual(response.data[0]['data'], self.certificate_log_2.data)
        self.assertEqual(response.data[1]['data'], self.certificate_log_1.data)

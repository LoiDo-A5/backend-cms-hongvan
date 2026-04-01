from rest_framework import status
from artwork.factories.owner_certificate import OwnerCertificateFactory
from core.accounts.factories.user import UserFactory
from core.accounts.tests.api.base_user_test import BaseUserTest
from core.accounts.models.user import USER_ROLE
from activity_log.models import ArtworkLog
from activity_log.models.artwork_log import ACTION_UPDATE_ARTWORK


class TransferOwnerForRoleArtistApiTest(BaseUserTest):
    def setUp(self) -> None:
        super().setUp()
        self.user.role = USER_ROLE.ARTIST
        self.user.save()
        self.owner_certificate = OwnerCertificateFactory()
        self.certificate = self.owner_certificate.certificate
        self.edition = self.certificate.artwork_edition
        self.artwork = self.edition.artwork
        self.certificate.issued_to = self.user
        self.certificate.issued_by = self.user
        self.certificate.save()
        self.url = f'/api/artwork/certificate/{self.certificate.code}/transfer_owner_role_artist/'

    def test_transfer_owner_artist_success(self):
        recipient = UserFactory()
        response = self.client.post(
            self.url,
            data={'recipient_user_id': recipient.id},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.certificate.refresh_from_db()
        self.assertEqual(self.certificate.issued_to_id, recipient.id)
        self.artwork.refresh_from_db()
        self.edition.refresh_from_db()
        self.assertEqual(self.artwork.status, 'sold')
        self.assertEqual(self.edition.status, 'sold')

        from artwork.models import ArtWork
        artwork_copies = ArtWork.all_objects.filter(linked_artwork=self.artwork, status='in_stock')
        self.assertGreaterEqual(artwork_copies.count(), 1)
        edition_copies = sum([ac.editions.filter(status='in_stock').count() for ac in artwork_copies])
        self.assertGreaterEqual(edition_copies, 1)

    def test_artwork_logs_created_on_artist_transfer(self):
        recipient = UserFactory()

        response = self.client.post(
            self.url,
            data={'recipient_user_id': recipient.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        logs = ArtworkLog.objects.filter(artwork=self.artwork).order_by('created_at')

        send_log = logs.filter(user=self.user, action_type=ACTION_UPDATE_ARTWORK).first()
        recv_log = logs.filter(user=recipient, action_type=ACTION_UPDATE_ARTWORK).first()

        self.assertIsNotNone(send_log)
        self.assertIsNotNone(recv_log)

        self.assertIn('Transferred ownership', send_log.content_en)
        self.assertIn('Received ownership', recv_log.content_en)

    def test_transfer_owner_artist_invalid_flow_issued_by_not_equal_issued_to(self):
        other_user = UserFactory()
        self.certificate.issued_by = other_user
        self.certificate.save(update_fields=['issued_by'])
        recipient = UserFactory()
        response = self.client.post(
            self.url,
            data={'recipient_user_id': recipient.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You do not have permission to transfer this certificate', str(response.data))

    def test_transfer_owner_artist_missing_recipient(self):
        response = self.client.post(
            self.url,
            data={},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'recipient_user_id': ['This field is required.']})

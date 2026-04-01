from rest_framework import status

from artwork.factories.artwork import ArtworkFactory
from artwork.factories.artwork_certificate import ArtworkCertificateFactory
from artwork.factories.artwork_edition import ArtworkEditionFactory
from artwork.factories.owner_certificate import OwnerCertificateFactory
from core.accounts.factories.user import UserFactory
from core.accounts.tests.api.base_user_test import BaseUserTest
from core.accounts.models.user import USER_ROLE
from activity_log.models import ArtworkLog
from activity_log.models.artwork_log import ACTION_UPDATE_ARTWORK


class TransferOwnerApiTest(BaseUserTest):
    def setUp(self) -> None:
        super().setUp()
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()

        self.owner_certificate = OwnerCertificateFactory()
        self.certificate = self.owner_certificate.certificate
        self.edition = self.certificate.artwork_edition
        self.artwork = self.edition.artwork

        self.certificate.issued_to = self.user
        self.certificate.save()
        self.artwork.owner = self.user
        self.artwork.save()

        self.url = f'/api/artwork/certificate/{self.certificate.code}/transfer_owner/'

    def test_transfer_owner_success_updates_certificate_and_artwork(self):
        recipient = UserFactory()
        recipient.legal_name = recipient.name or 'Recipient'
        recipient.save(update_fields=['legal_name'])

        response = self.client.post(
            self.url,
            data={
                'recipient_user_id': recipient.id,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.certificate.refresh_from_db()
        self.artwork.refresh_from_db()
        self.assertEqual(self.certificate.issued_to_id, recipient.id)
        self.assertEqual(self.artwork.owner_id, recipient.id)
        self.artwork.refresh_from_db()
        self.assertEqual(self.artwork.status, 'in_stock')
        self.assertTrue(response.data.get('success'))
        self.assertEqual(response.data.get('to_user_id'), recipient.id)

    def test_artwork_logs_created_on_transfer(self):
        recipient = UserFactory()
        recipient.legal_name = recipient.name
        recipient.save(update_fields=['legal_name'])

        response = self.client.post(
            self.url,
            data={'recipient_user_id': recipient.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        logs = ArtworkLog.objects.filter(artwork=self.artwork).order_by('created_at')
        self.assertEqual(logs.count(), 6)

        send_log = logs.filter(user=self.user, action_type=ACTION_UPDATE_ARTWORK).first()
        recv_log = logs.filter(user=recipient, action_type=ACTION_UPDATE_ARTWORK).first()

        self.assertIsNotNone(send_log)
        self.assertIsNotNone(recv_log)

        self.assertIn('Transferred ownership', send_log.content_en)
        self.assertIn('Received ownership', recv_log.content_en)

    def test_transfer_owner_forbidden_when_not_owner(self):
        other_owner = UserFactory()
        recipient = UserFactory()

        self.certificate.issued_to = other_owner
        self.certificate.save()
        self.artwork.owner = other_owner
        self.artwork.save()

        response = self.client.post(
            self.url,
            data={'recipient_user_id': recipient.id},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('You are not the current owner', response.data.get('message', ''))

    def test_transfer_owner_bad_request_missing_recipient(self):
        response = self.client.post(
            self.url,
            data={},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'recipient_user_id': ['This field is required.']})

    def test_transfer_owner_cannot_transfer_to_self(self):
        response = self.client.post(
            self.url,
            data={'recipient_user_id': self.user.id},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'message': ['Recipient must be different from current owner']})

    def test_transfer_owner_forbidden_when_current_user_is_artist_role(self):
        recipient = UserFactory()
        self.user.role = USER_ROLE.ARTIST
        self.user.save(update_fields=['role'])
        self.certificate.issued_to = self.user
        self.certificate.save(update_fields=['issued_to'])

        response = self.client.post(
            self.url,
            data={'recipient_user_id': recipient.id},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('Artist role is not allowed', response.data.get('message', ''))

    def test_transfer_owner_when_user_request_certificate_is_collector(self):
        from artwork.models import ArtWork

        artist = UserFactory(role=USER_ROLE.ARTIST)
        artwork = ArtworkFactory(owner=artist)
        edition = ArtworkEditionFactory(artwork=artwork)

        self.certificate.issued_by = artist
        self.certificate.save(update_fields=['issued_by'])

        self.artwork.linked_artwork = artwork
        self.artwork.save(update_fields=['linked_artwork'])

        self.edition.linked_edition = edition
        self.edition.save()

        recipient = UserFactory()
        recipient.legal_name = recipient.name or 'Recipient'
        recipient.save(update_fields=['legal_name'])

        response = self.client.post(
            self.url,
            data={
                'recipient_user_id': recipient.id,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        artist_artwork = ArtWork.objects.filter(owner=artist).count()
        self.assertEqual(artist_artwork, 1)

        collector_artwork = ArtWork.objects.filter(owner=self.user).count()
        self.assertEqual(collector_artwork, 0)

        recipient_artwork = ArtWork.all_objects.filter(owner=recipient, active=True, status='in_stock').count()
        self.assertEqual(recipient_artwork, 1)

    def test_transfer_owner_creates_collector_ownership_transfer_record(self):
        from artwork.models.collector_ownership_transfer import CollectorOwnershipTransfer

        recipient = UserFactory()
        recipient.legal_name = recipient.name or 'Recipient'
        recipient.save(update_fields=['legal_name'])

        response = self.client.post(
            self.url,
            data={'recipient_user_id': recipient.id},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(CollectorOwnershipTransfer.objects.filter(transferrer=self.user).count(), 1)

    def test_transfer_owner_no_collector_role_does_not_create_transfer_record(self):
        from artwork.models.collector_ownership_transfer import CollectorOwnershipTransfer

        recipient = UserFactory()
        recipient.legal_name = recipient.name or 'Recipient'
        recipient.save(update_fields=['legal_name'])

        self.user.role = USER_ROLE.SERVICE_PROVIDER
        self.user.save(update_fields=['role'])
        self.certificate.issued_to = self.user
        self.certificate.save(update_fields=['issued_to'])

        response = self.client.post(
            self.url,
            data={'recipient_user_id': recipient.id},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(CollectorOwnershipTransfer.objects.filter(transferrer=self.user).count(), 0)

    def test_transfer_owner_when_user_create_certificate_is_artist(self):
        from artwork.models import ArtWork

        artist = UserFactory(role=USER_ROLE.ARTIST)
        artwork = ArtworkFactory(owner=artist)
        edition = ArtworkEditionFactory(artwork=artwork)
        certificate = ArtworkCertificateFactory(artwork_edition=edition, issued_by=artist, issued_to=self.user)
        OwnerCertificateFactory(certificate=certificate)

        collector_artwork = ArtworkFactory(linked_artwork=artwork, owner=self.user)
        ArtworkEditionFactory(artwork=collector_artwork, linked_edition=edition)

        collector_artwork = ArtWork.objects.filter(owner=self.user).count()
        self.assertEqual(collector_artwork, 2)

        recipient = UserFactory()
        recipient.legal_name = recipient.name or 'Recipient'
        recipient.save(update_fields=['legal_name'])

        response = self.client.post(
            f'/api/artwork/certificate/{certificate.code}/transfer_owner/',
            data={
                'recipient_user_id': recipient.id,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        artist_artwork = ArtWork.objects.filter(owner=artist).count()
        self.assertEqual(artist_artwork, 1)

        collector_artwork = ArtWork.objects.filter(owner=self.user).count()
        self.assertEqual(collector_artwork, 1)

        recipient_artwork = ArtWork.all_objects.filter(owner=recipient, active=True, status='in_stock').count()
        self.assertEqual(recipient_artwork, 1)

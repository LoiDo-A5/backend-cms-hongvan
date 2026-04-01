from rest_framework import status

from artwork.factories.artwork import ArtworkFactory
from artwork.factories.artwork_edition import ArtworkEditionFactory
from artwork.factories.artwork_certificate import ArtworkCertificateFactory
from core.accounts.factories.user import UserFactory
from core.accounts.tests.api.base_user_test import BaseUserTest
from core.accounts.models.user import USER_ROLE
from activity_log.models import ArtworkLog
from activity_log.models.artwork_log import ACTION_UPDATE_ARTWORK
from artwork.models.artwork import ArtWork
from artwork.models import ArtworkEdition


class TransferOwnerArtworkForRoleArtistApiTest(BaseUserTest):
    def setUp(self) -> None:
        super().setUp()
        self.user.role = USER_ROLE.ARTIST
        self.user.save()
        self.base_artwork = ArtworkFactory(owner=self.user, status='available')
        self.base_edition = ArtworkEditionFactory(artwork=self.base_artwork, edition_number=1, status='available')
        self.url = '/api/artwork/transfer_owner_artwork_role_artist/'

    def test_transfer_owner_artwork_artist_success(self):
        recipient = UserFactory()
        response = self.client.post(
            self.url,
            data={
                'edition_id': self.base_edition.id,
                'recipient_user_id': recipient.id,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['from_user_id'], self.user.id)
        self.assertEqual(data['to_user_id'], recipient.id)

        artwork_copies = ArtWork.all_objects.filter(linked_artwork=self.base_artwork, owner=recipient)
        self.assertEqual(artwork_copies.count(), 1)
        artwork_copy = artwork_copies.first()
        self.assertEqual(data['artwork_id'], artwork_copy.id)
        self.assertEqual(artwork_copy.status, 'in_stock')

        edition_copies = ArtworkEdition.objects.filter(artwork=artwork_copy, linked_edition=self.base_edition)
        self.assertEqual(edition_copies.count(), 1)
        self.assertEqual(edition_copies.first().status, 'in_stock')

        logs = ArtworkLog.objects.filter(artwork=self.base_artwork).order_by('created_at')
        self.assertTrue(logs.filter(user=self.user, action_type=ACTION_UPDATE_ARTWORK).exists())
        self.assertTrue(logs.filter(user=recipient, action_type=ACTION_UPDATE_ARTWORK).exists())

    def test_transfer_owner_artwork_artist_missing_fields(self):
        response = self.client.post(
            self.url,
            data={},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('edition_id', response.json())
        self.assertIn('recipient_user_id', response.json())

    def test_transfer_owner_artwork_artist_invalid_role(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save(update_fields=['role'])
        recipient = UserFactory()
        response = self.client.post(
            self.url,
            data={
                'edition_id': self.base_edition.id,
                'recipient_user_id': recipient.id,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You do not have permission to transfer this artwork', str(response.data))

    def test_transfer_owner_artwork_artist_edition_has_certificate(self):
        ArtworkCertificateFactory(artwork_edition=self.base_edition)
        recipient = UserFactory()
        response = self.client.post(
            self.url,
            data={
                'edition_id': self.base_edition.id,
                'recipient_user_id': recipient.id,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Edition already has a certificate and cannot be transferred', str(response.data))

    def test_transfer_owner_artwork_artist_edition_already_linked(self):
        other_artwork = ArtworkFactory(owner=self.user)
        linked_copy = ArtworkEditionFactory(artwork=other_artwork, status='available')
        linked_copy.linked_edition = self.base_edition
        linked_copy.save()
        recipient = UserFactory()
        response = self.client.post(
            self.url,
            data={
                'edition_id': self.base_edition.id,
                'recipient_user_id': recipient.id,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('already been linked', str(response.data))

    def test_transfer_owner_artwork_artist_not_owner_of_artwork(self):
        other_user = UserFactory()
        self.base_artwork.owner = other_user
        self.base_artwork.save(update_fields=['owner'])
        recipient = UserFactory()
        response = self.client.post(
            self.url,
            data={
                'edition_id': self.base_edition.id,
                'recipient_user_id': recipient.id,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('You are not the owner of this artwork', str(response.data))

from rest_framework import status

from artwork.factories.artwork import ArtworkFactory
from artwork.models.collector_ownership_transfer import CollectorOwnershipTransfer
from core.accounts.factories.user import UserFactory
from core.accounts.models.user import USER_ROLE
from core.accounts.tests.api.base_user_test import BaseUserTest


class ArtworkUpdateTransferTest(BaseUserTest):
    def setUp(self) -> None:
        super().setUp()
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save(update_fields=['role'])

    def test_collector_change_owner_creates_transfer_record(self):
        artwork = ArtworkFactory(owner=self.user)
        recipient = UserFactory()

        url = f'/api/artwork/artwork/{artwork.uuid}/'
        response = self.client.patch(url, data={'owner': recipient.id}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            CollectorOwnershipTransfer.objects.filter(
                transferrer=self.user, transferee=recipient, artwork_id=artwork.id,
            ).count(),
            1,
        )

    def test_no_record_created_when_recipient_is_same_as_current_owner(self):
        artwork = ArtworkFactory(owner=self.user)

        url = f'/api/artwork/artwork/{artwork.uuid}/'
        response = self.client.patch(url, data={'owner': self.user.id}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(CollectorOwnershipTransfer.objects.filter(transferrer=self.user).count(), 0)

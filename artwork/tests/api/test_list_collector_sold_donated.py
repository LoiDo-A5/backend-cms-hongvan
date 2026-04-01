from datetime import timedelta

from django.utils import timezone
from rest_framework import status

from artwork.factories.artwork import ArtworkFactory
from artwork.models import ArtWork
from artwork.models.collector_ownership_transfer import CollectorOwnershipTransfer
from core.accounts.factories.user import UserFactory
from core.accounts.models.user import USER_ROLE
from core.accounts.tests.api.base_user_test import BaseUserTest


class ListCollectorSoldDonatedApiTest(BaseUserTest):
    def setUp(self) -> None:
        super().setUp()
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save(update_fields=['role'])
        self.url = '/api/artwork/artwork/list_collector_sold_donated/'

    def test_permission_denied_when_not_collector_or_unauthenticated(self):
        self.user.role = USER_ROLE.ARTIST
        self.user.save(update_fields=['role'])
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.credentials()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_returns_combined_results_with_search_and_empty_page_fallback(self):
        a1 = ArtworkFactory(owner=self.user, status='sold')
        a2 = ArtworkFactory(owner=self.user, status='donated_gifted')

        ArtWork.objects.filter(pk=a1.pk).update(updated_at=timezone.now() - timedelta(days=2))
        ArtWork.objects.filter(pk=a2.pk).update(updated_at=timezone.now() - timedelta(days=1))

        transferee = UserFactory()
        t1 = CollectorOwnershipTransfer.objects.create(
            transferrer=self.user,
            transferee=transferee,
            artwork=a1,
            certificate=None,
            snapshot={'title': 'Alpha Piece', 'inventory_code': 'INV-001'},
        )
        t2 = CollectorOwnershipTransfer.objects.create(
            transferrer=self.user,
            transferee=transferee,
            artwork=a2,
            certificate=None,
            snapshot={'title': 'Beta Work', 'inventory_code': 'INV-002'},
        )
        CollectorOwnershipTransfer.objects.filter(pk=t1.pk).update(
            transferred_at=timezone.now() - timedelta(hours=12),
        )
        CollectorOwnershipTransfer.objects.filter(pk=t2.pk).update(
            transferred_at=timezone.now() - timedelta(hours=6),
        )

        response = self.client.get(self.url, {'search': 'Alpha', 'page': 2}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data['count'], 1)
        self.assertEqual(len(response.data['results']), 1)

        kinds = [row.get('is_ownership_transfer_record', False) for row in response.data['results']]
        self.assertEqual(kinds, [True])

        transfer_rows = [r for r in response.data['results'] if r.get('is_ownership_transfer_record')]
        self.assertEqual(len(transfer_rows), 1)
        self.assertEqual(transfer_rows[0]['ownership_transfer_id'], t1.id)
        self.assertIsNotNone(transfer_rows[0]['transferee'])

    def test_returns_results_without_search_valid_page(self):
        a1 = ArtworkFactory(owner=self.user, status='sold')
        ArtworkFactory(owner=self.user, status='donated_gifted')

        transferee = UserFactory()
        CollectorOwnershipTransfer.objects.create(
            transferrer=self.user,
            transferee=transferee,
            artwork=a1,
            certificate=None,
            snapshot={'title': 'Gamma', 'inventory_code': 'INV-003'},
        )

        response = self.client.get(self.url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 3)
        self.assertEqual(len(response.data['results']), 3)

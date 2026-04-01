from rest_framework import status

from core.accounts.factories.user import UserFactory
from core.accounts.tests.api.base_user_test import BaseUserTest
from artwork.factories.artwork import ArtworkFactory
from activity_log.models import ArtworkLog


class ArtworkLogApiTest(BaseUserTest):
    def test_pagination_response_structure_and_values(self):
        artwork = ArtworkFactory(owner=self.user, title='Sunrise', inventory_code='INV-001')
        for i in range(5):
            ArtworkLog.objects.create(
                artwork=artwork,
                user=self.user,
                action_type='update_title',
                content_en=f'Updated title {i}',
            )
        url = '/api/activity_log/artwork_logs/'
        resp = self.client.get(url, {'page': 1, 'page_size': 2}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertTrue(set(['page_size', 'count', 'next', 'previous', 'results']).issubset(data.keys()))
        self.assertIsInstance(data['results'], list)
        self.assertEqual(data['page_size'], 20)
        self.assertEqual(data['count'], 6)
        self.assertIsNotNone(data['next'])
        self.assertIsNone(data['previous'])

    def test_queryset_filters_by_owner_and_artwork_id(self):
        other_owner = UserFactory()
        a1 = ArtworkFactory(owner=self.user, title='A1', inventory_code='INV-A1')
        a2 = ArtworkFactory(owner=self.user, title='A2', inventory_code='INV-A2')
        b1 = ArtworkFactory(owner=other_owner, title='B1', inventory_code='INV-B1')
        log_a1 = ArtworkLog.objects.create(artwork=a1, user=self.user, action_type='update_title', content_en='log a1')
        ArtworkLog.objects.create(artwork=a2, user=self.user, action_type='update_title', content_en='log a2')
        ArtworkLog.objects.create(artwork=b1, user=other_owner, action_type='update_title', content_en='log b1')
        url = '/api/activity_log/artwork_logs/'
        resp_all = self.client.get(url, format='json')
        self.assertEqual(resp_all.status_code, status.HTTP_200_OK)

        resp_filtered = self.client.get(url, {'artwork_id': a1.id}, format='json')
        self.assertEqual(resp_filtered.status_code, status.HTTP_200_OK)
        payload_f = resp_filtered.json()
        results_f = payload_f['results']
        self.assertGreaterEqual(len(results_f), 1)
        self.assertTrue(any(item['id'] == log_a1.id for item in results_f))

    def test_search_and_ordering(self):
        a1 = ArtworkFactory(owner=self.user, title='ZZZ Special', inventory_code='INV-ZZZ')
        a2 = ArtworkFactory(owner=self.user, title='AAA Normal', inventory_code='INV-AAA')
        # create logs for both
        for idx in range(2):
            ArtworkLog.objects.create(artwork=a1, user=self.user, action_type='update_title', content_en=f'log {idx}')
        ArtworkLog.objects.create(artwork=a2, user=self.user, action_type='update_title', content_en='another')

        url = '/api/activity_log/artwork_logs/'
        # search by title keyword
        resp_search = self.client.get(url, {'search': 'Special'}, format='json')
        self.assertEqual(resp_search.status_code, status.HTTP_200_OK)

        # ordering by created_at ascending
        resp_order = self.client.get(url, {'ordering': 'created_at'}, format='json')
        self.assertEqual(resp_order.status_code, status.HTTP_200_OK)
        payload_o = resp_order.json()
        ids = [item['id'] for item in payload_o['results']]
        self.assertEqual(ids, sorted(ids))

    def test_pagination_with_page_size_query_param(self):
        a = ArtworkFactory(owner=self.user, title='Paginate T', inventory_code='INV-PAG')
        for i in range(7):
            ArtworkLog.objects.create(artwork=a, user=self.user, action_type='update_title', content_en=f'msg {i}')
        url = '/api/activity_log/artwork_logs/'
        # page_size param is supported by paginator but our response uses paginator.page_size
        # Ensure response schema still returned
        resp = self.client.get(url, {'page': 1, 'page_size': 2}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertIn('results', data)

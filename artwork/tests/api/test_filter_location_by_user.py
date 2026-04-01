from rest_framework import status

from core.accounts.factories.user import UserLocationFactory
from core.accounts.tests.api.base_user_test import BaseUserTest


class FilterLocationApiTests(BaseUserTest):
    def setUp(self) -> None:
        super().setUp()
        self.location_1 = UserLocationFactory(user=self.user)
        self.location_2 = UserLocationFactory(user=self.user)
        self.location_3 = UserLocationFactory()

    def test_filter_location(self):
        response = self.client.get(
            '/api/artwork/filters/location/', {
                'user': self.user.id,
            }, format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['id'], self.location_2.id)
        self.assertEqual(response.data[1]['id'], self.location_1.id)

from rest_framework import status

from core.accounts.factories.user import UserLocationFactory
from core.accounts.models import UserLocation
from core.accounts.tests.api.base_user_test import BaseUserTest


class LocationApiTest(BaseUserTest):
    def test_create_location(self):
        response = self.client.post(
            '/api/accounts/location/', {
                'user': self.user.id,
                'location': 'Test Location',
            },
        )
        user_location = UserLocation.objects.all()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(user_location), 1)
        self.assertEqual(user_location[0].user, self.user)
        self.assertEqual(user_location[0].location, 'Test Location')

    def test_delete_location(self):
        user_location = UserLocationFactory(user=self.user)
        response = self.client.delete(f'/api/accounts/location/{user_location.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserLocation.objects.filter(id=user_location.id))

    def test_get_user_location(self):
        user_location1 = UserLocationFactory(user=self.user)
        user_location2 = UserLocationFactory(user=self.user)
        UserLocationFactory()

        response = self.client.get('/api/accounts/location/', format='json')
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['location'], user_location1.location)
        self.assertEqual(response.data[1]['location'], user_location2.location)

    def test_create_duplicate_location(self):
        UserLocationFactory(user=self.user, location='Test Location')

        response = self.client.post(
            '/api/accounts/location/', {
                'user': self.user.id,
                'location': 'Test Location',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Location name already exists in your list.', response.data['location'][0])

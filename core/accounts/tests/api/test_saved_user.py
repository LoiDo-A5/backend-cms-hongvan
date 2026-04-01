from core.accounts.factories.user import UserFactory
from core.accounts.factories.user import SavedUserFactory
from core.accounts.models import SavedUser
from core.accounts.models.user import USER_ROLE
from core.accounts.tests.api.base_user_test import BaseUserTest
from rest_framework import status


class SavedUserApiTest(BaseUserTest):
    def test_create_saved_user(self):
        another_user = UserFactory(role=USER_ROLE.COLLECTOR)
        response = self.client.post(
            '/api/accounts/saved_user/', {
                'user': self.user.id,
                'saved_user': another_user.id,
            },
        )
        saved_users = SavedUser.objects.all()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(saved_users), 1)
        self.assertEqual(saved_users[0].user, self.user)
        self.assertEqual(saved_users[0].saved_user, another_user)

    def test_get_saved_users(self):
        SavedUserFactory(user=self.user)
        SavedUserFactory()

        response = self.client.get('/api/accounts/saved_user/', format='json')
        self.assertEqual(len(response.data), 1)

    def test_create_duplicate_saved_user(self):
        another_user = UserFactory(role=USER_ROLE.COLLECTOR)
        SavedUserFactory(user=self.user, saved_user=another_user)

        response = self.client.post(
            '/api/accounts/saved_user/', {
                'user': self.user.id,
                'saved_user': another_user.id,
            },
        )
        saved_users = SavedUser.objects.all()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(saved_users), 1)
        self.assertEqual(saved_users[0].user, self.user)
        self.assertEqual(saved_users[0].saved_user, another_user)

    def test_get_saved_users_with_roles(self):
        another_artist = UserFactory(role=USER_ROLE.ARTIST)
        another_collector = UserFactory(role=USER_ROLE.COLLECTOR)
        SavedUserFactory(user=self.user, saved_user=another_artist)
        SavedUserFactory(user=self.user, saved_user=another_collector)

        response = self.client.get('/api/accounts/saved_user/?role=1,4d', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        saved_user_roles = [saved_user['saved_user']['role'] for saved_user in response.data]
        self.assertIn(USER_ROLE.ARTIST, saved_user_roles)
        self.assertIn(USER_ROLE.COLLECTOR, saved_user_roles)

    def test_delete_old_saved_users(self):
        for _ in range(11):
            another_user = UserFactory(role=USER_ROLE.COLLECTOR)
            SavedUserFactory(user=self.user, saved_user=another_user)

        saved_users = SavedUser.objects.filter(user=self.user).order_by('-created_at')
        self.assertEqual(len(saved_users), 11)

        new_user = UserFactory(role=USER_ROLE.COLLECTOR)
        response = self.client.post(
            '/api/accounts/saved_user/', {
                'user': self.user.id,
                'saved_user': new_user.id,
            },
        )

        saved_users = SavedUser.objects.filter(user=self.user).order_by('-created_at')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(saved_users), 12)
        self.assertIn(new_user, [saved_user.saved_user for saved_user in saved_users])
        self.assertNotIn(saved_users.last(), [saved_user.saved_user for saved_user in saved_users])

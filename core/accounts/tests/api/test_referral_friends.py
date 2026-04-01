from rest_framework import status

from core.accounts.factories.user import UserFactory
from core.accounts.tests.api.base_user_test import BaseUserTest


class ReferralFriendsApiTests(BaseUserTest):
    def test_get_referral_friends_no_plan(self):
        friend1, friend2 = UserFactory.create_batch(2, referred_by=self.user)
        response = self.client.get('/api/accounts/referral_friends/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        data_friend2 = response.data[0]
        self.assertEqual(data_friend2['id'], friend2.id)
        self.assertIn('name', data_friend2)
        self.assertIn('email', data_friend2)

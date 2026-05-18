from django.contrib.auth.models import Permission, Group
from rest_framework import status

from core.accounts.tests.api.base_user_test import BaseUserTest


class FeaturesApiTests(BaseUserTest):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.add_user_perm = Permission.objects.get_by_natural_key('add_user', 'accounts', 'user')

    def test_get_all_features(self):
        self.user.user_permissions.add(self.add_user_perm)

        self._assert_found_assign_feature()

    def test_get_all_features_by_group(self):
        group = Group.objects.create(name='test_group')
        group.permissions.add(self.add_user_perm)
        group.user_set.add(self.user)

        self._assert_found_assign_feature()

    def _assert_found_assign_feature(self):
        response = self.client.get('/api/accounts/features/')
        self.assertResponseStatus(response, status.HTTP_200_OK)
        self.assertNotIn('add_user', response.data)

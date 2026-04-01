from rest_framework import status

from core.accounts.tests.api.base_user_test import BaseUserTest
from core.accounts.models import UserVisibleSetting


class UserVisibleSettingApiTest(BaseUserTest):
    def test_user_update_setting(self):
        response = self.client.patch('/api/accounts/user_visible_setting/', {
            'is_public_social_media': False,
            'is_public_artwork': False,
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user_setting = UserVisibleSetting.objects.first()
        self.assertEqual(user_setting.user, self.user)
        self.assertFalse(user_setting.is_public_social_media)
        self.assertFalse(user_setting.is_public_artwork)

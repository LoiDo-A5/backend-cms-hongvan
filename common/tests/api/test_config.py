from django.core.cache import cache
from rest_framework import status

from common.tests.isolated_cache_test_case import APITestCase


class ConfigApiTest(APITestCase):
    def tearDown(self) -> None:
        cache.delete('FORCE_UPGRADE_VERSION_IOS')
        cache.delete('FORCE_UPGRADE_VERSION_ANDROID')

    def test_config_must_upgrade_ios(self):
        cache.set('FORCE_UPGRADE_VERSION_IOS', '2.0.0')
        response = self.client.get(
            '/api/common/config/ios/', {
                'version': '1.0.0',
            },
        )
        self.assertResponseStatus(response, status.HTTP_200_OK)
        self.assertTrue(response.data['upgrade'])

    def test_config_not_upgrade_ios(self):
        cache.set('FORCE_UPGRADE_VERSION_IOS', '2.0.0')
        response = self.client.get(
            '/api/common/config/ios/', {
                'version': '3.0.0',
            },
        )
        self.assertResponseStatus(response, status.HTTP_200_OK)
        self.assertFalse(response.data['upgrade'])

    def test_config_not_upgrade_ios_not_set(self):
        response = self.client.get(
            '/api/common/config/ios/', {
                'version': '3.0.0',
            },
        )
        self.assertResponseStatus(response, status.HTTP_200_OK)
        self.assertFalse(response.data['upgrade'])

    def test_config_must_upgrade_android(self):
        cache.set('FORCE_UPGRADE_VERSION_ANDROID', '2.0.0')
        response = self.client.get(
            '/api/common/config/android/', {
                'version': '1.0.0',
            },
        )
        self.assertResponseStatus(response, status.HTTP_200_OK)
        self.assertTrue(response.data['upgrade'])

    def test_config_not_upgrade_android(self):
        cache.set('FORCE_UPGRADE_VERSION_ANDROID', '2.0.0')
        response = self.client.get(
            '/api/common/config/android/', {
                'version': '3.0.0',
            },
        )
        self.assertResponseStatus(response, status.HTTP_200_OK)
        self.assertFalse(response.data['upgrade'])

    def test_config_not_upgrade_android_not_set(self):
        response = self.client.get(
            '/api/common/config/android/', {
                'version': '3.0.0',
            },
        )
        self.assertResponseStatus(response, status.HTTP_200_OK)
        self.assertFalse(response.data['upgrade'])

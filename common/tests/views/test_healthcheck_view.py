from rest_framework import status

from common.tests.isolated_cache_test_case import TestCase


class HealthCheckViewTests(TestCase):
    def test_health_check(self):
        response = self.client.get('/healthcheck/')
        self.assertResponseStatus(response, status.HTTP_200_OK)


class HealthCheckViewNoDbTests(TestCase):
    def test_health_check_skip_db(self):
        response = self.client.get(
            '/healthcheck/', {
                'skip_db': 1,
            },
        )
        self.assertResponseStatus(response, status.HTTP_200_OK)

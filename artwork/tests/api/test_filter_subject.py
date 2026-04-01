from rest_framework import status

from artwork.factories.subject_artwork import SubjectArtworkFactory
from core.accounts.tests.api.base_user_test import BaseUserTest


class SubjectArtworkFilterApiTests(BaseUserTest):
    def setUp(self) -> None:
        super().setUp()
        self.subject1 = SubjectArtworkFactory(category='sculpture')
        self.subject2 = SubjectArtworkFactory(category='painting')
        self.subject3 = SubjectArtworkFactory(category='painting')

    def test_filter_subject_success(self):
        response = self.client.get(
            '/api/artwork/filters/subject/', {
                'category': 'sculpture',
            }, format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['category'], self.subject1.category)

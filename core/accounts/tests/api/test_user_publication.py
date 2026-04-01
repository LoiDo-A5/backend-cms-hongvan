from faker import Faker
from rest_framework import status

from core.accounts.factories.user import UserPublicationFactory
from core.accounts.models import UserPublication
from core.accounts.tests.api.base_user_test import BaseUserTest
from core.accounts.factories.user import UserFactory

faker = Faker()


class PublicationApiTest(BaseUserTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def test_create_publication(self):
        description = faker.paragraph()
        response = self.client.post(
            '/api/accounts/publication/',
            data={
                'year': '2000',
                'description': description,
                'is_public': True,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['description'], description)
        self.assertEqual(response.data['year'], 2000)
        self.assertEqual(response.data['is_public'], True)

    def test_get_user_publication(self):
        publication1 = UserPublicationFactory(user=self.user, year='2000')
        publication2 = UserPublicationFactory(user=self.user, year='2001')
        UserPublicationFactory()

        response = self.client.get('/api/accounts/publication/', format='json')
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['id'], publication1.id)
        self.assertEqual(response.data[0]['user'], publication1.user.id)
        self.assertEqual(response.data[1]['id'], publication2.id)
        self.assertEqual(response.data[1]['year'], 2001)

    def test_get_public_publication(self):
        public_publication = UserPublicationFactory(user=self.user, year='2002', is_public=True)
        UserPublicationFactory(user=self.user, year='2003', is_public=False)

        response = self.client.get('/api/accounts/publication/', format='json', data={'is_public': True})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], public_publication.id)
        self.assertEqual(response.data[0]['year'], 2002)
        self.assertEqual(response.data[0]['is_public'], True)

    def test_get_user_view_another_user_publication(self):
        user_2 = UserFactory()

        public_publication = UserPublicationFactory(user=user_2, year='2002', is_public=True)
        UserPublicationFactory(user=user_2, year='2003', is_public=False)

        UserPublicationFactory(user=self.user, year='2003', is_public=True)

        response = self.client.get(
            '/api/accounts/publication/',
            data={
                'is_public': True,
                'user_uuid': user_2.uuid,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], public_publication.id)
        self.assertEqual(response.data[0]['year'], 2002)
        self.assertEqual(response.data[0]['is_public'], True)

    def test_detail_publication(self):
        publication = UserPublicationFactory(user=self.user)

        response = self.client.get(f'/api/accounts/publication/{publication.id}/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], publication.id)
        self.assertEqual(response.data['user'], publication.user.id)

    def test_update_publication(self):
        publication = UserPublicationFactory(user=self.user, year='2000')

        response = self.client.patch(
            f'/api/accounts/publication/{publication.id}/', {
                'year': '2020',
                'description': 'update description',
                'is_public': False,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['year'], 2020)
        self.assertEqual(response.data['description'], 'update description')
        self.assertEqual(response.data['is_public'], False)

    def test_delete_publication(self):
        publication = UserPublicationFactory(user=self.user)

        response = self.client.delete(f'/api/accounts/publication/{publication.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserPublication.objects.filter(id=publication.id).exists())

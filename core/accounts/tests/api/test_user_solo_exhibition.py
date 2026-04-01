from faker import Faker
from rest_framework import status

from core.accounts.factories.user import UserSoloExhibitionFactory
from core.accounts.models import UserSoloExhibition
from core.accounts.tests.api.base_user_test import BaseUserTest
from core.accounts.factories.user import UserFactory

faker = Faker()


class SoloExhibitionApiTest(BaseUserTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def test_create_solo_exhibition(self):
        description = faker.paragraph()
        link = faker.uri()
        response = self.client.post(
            '/api/accounts/solo_exhibition/',
            data={
                'year': '2000',
                'description': description,
                'is_public': True,
                'exhibition_link': link,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['description'], description)
        self.assertEqual(response.data['year'], 2000)
        self.assertEqual(response.data['is_public'], True)
        self.assertEqual(response.data['exhibition_link'], link)

    def test_get_user_solo_exhibition(self):
        exhibition1 = UserSoloExhibitionFactory(user=self.user, year='2000')
        exhibition2 = UserSoloExhibitionFactory(user=self.user, year='2001')
        UserSoloExhibitionFactory()

        response = self.client.get('/api/accounts/solo_exhibition/', format='json')
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['id'], exhibition1.id)
        self.assertEqual(response.data[0]['user'], exhibition1.user.id)
        self.assertEqual(response.data[1]['id'], exhibition2.id)
        self.assertEqual(response.data[1]['year'], 2001)

    def test_get_public_solo_exhibitions(self):
        public_exhibition = UserSoloExhibitionFactory(user=self.user, year='2002', is_public=True)
        UserSoloExhibitionFactory(user=self.user, year='2003', is_public=False)

        response = self.client.get('/api/accounts/solo_exhibition/', format='json', data={'is_public': True})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], public_exhibition.id)
        self.assertEqual(response.data[0]['year'], 2002)
        self.assertEqual(response.data[0]['is_public'], True)

    def test_get_user_view_another_user_solo_exhibitions(self):
        user_2 = UserFactory()

        public_exhibition = UserSoloExhibitionFactory(user=user_2, year='2002', is_public=True)
        UserSoloExhibitionFactory(user=user_2, year='2003', is_public=False)

        UserSoloExhibitionFactory(user=self.user, year='2003', is_public=True)

        response = self.client.get(
            '/api/accounts/solo_exhibition/',
            data={
                'is_public': True,
                'user_uuid': user_2.uuid,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], public_exhibition.id)
        self.assertEqual(response.data[0]['year'], 2002)
        self.assertEqual(response.data[0]['is_public'], True)

    def test_detail_solo_exhibition(self):
        exhibition = UserSoloExhibitionFactory(user=self.user)

        response = self.client.get(f'/api/accounts/solo_exhibition/{exhibition.id}/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], exhibition.id)
        self.assertEqual(response.data['user'], exhibition.user.id)

    def test_update_solo_exhibition(self):
        exhibition = UserSoloExhibitionFactory(user=self.user, year='2000')
        link = faker.uri()

        response = self.client.patch(
            f'/api/accounts/solo_exhibition/{exhibition.id}/', {
                'year': '2020',
                'description': 'update description',
                'is_public': False,
                'exhibition_link': link,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['year'], 2020)
        self.assertEqual(response.data['description'], 'update description')
        self.assertEqual(response.data['is_public'], False)
        self.assertEqual(response.data['exhibition_link'], link)

    def test_delete_solo_exhibition(self):
        exhibition = UserSoloExhibitionFactory(user=self.user)

        response = self.client.delete(f'/api/accounts/solo_exhibition/{exhibition.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserSoloExhibition.objects.filter(id=exhibition.id).exists())

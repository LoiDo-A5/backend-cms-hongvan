from faker import Faker
from rest_framework import status

from core.accounts.factories.image_award import ImageAwardFactory
from core.accounts.factories.user import UserAwardFactory
from core.accounts.models import ImageAward, UserAward
from core.accounts.tests.api.base_user_test import BaseUserTest
from core.accounts.factories.user import UserFactory

faker = Faker()


class AwardApiTest(BaseUserTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def test_create_award(self):
        description = faker.paragraph()
        images = [
            'image_1.png',
            'image_2.png',
        ]
        response = self.client.post(
            '/api/accounts/award/',
            data={
                'year': '2000',
                'description': description,
                'is_public': True,
                'images': images,
            },
            format='json',
        )

        image_award = ImageAward.objects.last()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['description'], description)
        self.assertEqual(response.data['year'], 2000)
        self.assertEqual(response.data['is_public'], True)

        self.assertEqual(image_award.image, 'image_2.png')

    def test_create_award_reach_limit(self):
        description = faker.paragraph()
        images = [
            'image_1.png',
            'image_2.png',
            'image_3.png',
            'image_4.png',
            'image_5.png',
            'image_6.png',
        ]
        response = self.client.post(
            '/api/accounts/award/',
            data={
                'year': '2000',
                'description': description,
                'is_public': True,
                'images': images,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'non_field_errors': ['Maximum 5 images are allowed.']})

    def test_get_user_award(self):
        award1 = UserAwardFactory(user=self.user, year='2000')
        award2 = UserAwardFactory(user=self.user, year='2001')
        UserAwardFactory()
        ImageAwardFactory(award=award1, image='image_1.png')
        ImageAwardFactory(award=award1)
        ImageAwardFactory(award=award2)

        response = self.client.get('/api/accounts/award/', format='json')
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['id'], award1.id)
        self.assertEqual(response.data[0]['user']['id'], award1.user.id)
        self.assertEqual(response.data[1]['id'], award2.id)
        self.assertEqual(response.data[0]['list_image'][0]['key_images'], 'image_1.png')

    def test_get_user_view_another_user_award(self):
        user_2 = UserFactory()
        award1 = UserAwardFactory(user=user_2, year='2000')
        UserAwardFactory(user=user_2, year='2001')

        UserAwardFactory(user=self.user)

        response = self.client.get('/api/accounts/award/', {'user_uuid': user_2.uuid}, format='json')
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['id'], award1.id)
        self.assertEqual(response.data[0]['user']['id'], award1.user.id)

    def test_get_public_awards(self):
        public_award = UserAwardFactory(user=self.user, is_public=True)
        UserAwardFactory(user=self.user, is_public=False)

        response = self.client.get('/api/accounts/award/', format='json', data={'is_public': True})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], public_award.id)
        self.assertEqual(response.data[0]['is_public'], True)

    def test_detail_award(self):
        award = UserAwardFactory(user=self.user)
        ImageAwardFactory(award=award)
        ImageAwardFactory(award=award)

        response = self.client.get(f'/api/accounts/award/{award.id}/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], award.id)
        self.assertEqual(response.data['user']['id'], award.user.id)

    def test_update_description_and_year_award(self):
        award = UserAwardFactory(user=self.user, year='2000')

        response = self.client.patch(
            f'/api/accounts/award/{award.id}/', {
                'year': '2020',
                'description': 'update description',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['year'], 2020)
        self.assertEqual(response.data['description'], 'update description')

    def test_update_images_award(self):
        award = UserAwardFactory(user=self.user, year='2000')
        ImageAwardFactory(award=award)
        ImageAwardFactory(award=award)
        images = [
            'image_1.png',
            'image_2.png',
            'image_3.png',
        ]

        response = self.client.patch(
            f'/api/accounts/award/{award.id}/', {
                'year': 2005,
                'description': 'update description',
                'is_public': False,
                'images': images,
            },
        )
        image_award = ImageAward.objects.filter(award=award)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['year'], 2005)
        self.assertEqual(response.data['description'], 'update description')
        self.assertEqual(response.data['is_public'], False)
        self.assertEqual(len(image_award), 3)
        self.assertEqual(image_award[0].image, images[0])
        self.assertEqual(image_award[1].image, images[1])

    def test_update_images_award_empty(self):
        award = UserAwardFactory(user=self.user, year='2000')
        ImageAwardFactory(award=award)
        ImageAwardFactory(award=award)
        images = []

        response = self.client.patch(
            f'/api/accounts/award/{award.id}/', {
                'year': 2005,
                'description': 'update description',
                'is_public': False,
                'images': images,
            },
        )
        image_award = ImageAward.objects.filter(award=award)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['year'], 2005)
        self.assertEqual(response.data['description'], 'update description')
        self.assertEqual(response.data['is_public'], False)
        self.assertEqual(len(image_award), 0)
        self.assertFalse(ImageAward.objects.filter(award=award).exists())

    def test_update_award_with_existing_images(self):
        award = UserAwardFactory(user=self.user, year='2000')
        ImageAwardFactory(award=award, image='image_1.png')
        ImageAwardFactory(award=award)
        images = [
            'image_1.png',
            'image_2.png',
            'image_3.png',
        ]

        response = self.client.patch(
            f'/api/accounts/award/{award.id}/', {
                'year': 2005,
                'description': 'update description',
                'is_public': False,
                'images': images,
            },
        )
        image_award = ImageAward.objects.filter(award=award)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['year'], 2005)
        self.assertEqual(response.data['description'], 'update description')
        self.assertEqual(response.data['is_public'], False)
        self.assertEqual(len(image_award), 3)
        self.assertEqual(image_award[0].image, images[0])
        self.assertEqual(image_award[1].image, images[1])

    def test_update_images_award_reach_limit(self):
        award = UserAwardFactory(user=self.user, year='2000')
        ImageAwardFactory(award=award, image='image_1.png')
        ImageAwardFactory(award=award)
        images = [
            'image_1.png',
            'image_2.png',
            'image_3.png',
            'image_4.png',
            'image_5.png',
            'image_6.png',
        ]

        response = self.client.patch(
            f'/api/accounts/award/{award.id}/', {
                'year': 2005,
                'description': 'update description',
                'is_public': False,
                'images': images,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'non_field_errors': ['Maximum 5 images are allowed.']})

    def test_delete_award(self):
        award = UserAwardFactory(user=self.user)
        ImageAwardFactory(award=award)
        ImageAwardFactory(award=award)

        response = self.client.delete(f'/api/accounts/award/{award.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserAward.objects.filter(id=award.id).exists())
        self.assertFalse(ImageAward.objects.filter(award=award).exists())

from rest_framework import status

from core.accounts.factories.user import UserProfileFactory
from core.accounts.factories.user import UserFactory
from core.accounts.tests.api.base_user_test import BaseUserTest


class UserProfileApiTest(BaseUserTest):
    def test_get_user_profile(self):
        user_profile = UserProfileFactory(user=self.user, image_portrait='image1.png')

        response = self.client.get('/api/accounts/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], user_profile.id)
        self.assertIn('http://testserver', response.data['image_portrait'])
        self.assertTrue(response.data['is_owner'])
        self.assertIn('avatar', response.data)
        self.assertIn('role', response.data)

    def test_get_user_profile_with_data_visible_setting(self):
        user_profile = UserProfileFactory(user=self.user, image_portrait='image1.png')

        response = self.client.get('/api/accounts/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], user_profile.id)

        self.assertIsNotNone(response.data['visible_setting'])
        visible_setting = response.data['visible_setting']
        self.assertTrue(visible_setting['is_public_social_media'])

    def test_get_user_view_another_user_profile(self):
        UserProfileFactory(user=self.user, image_portrait='image1.png')
        user_2 = UserFactory()

        response = self.client.get('/api/accounts/profile/', {
            'user_uuid': user_2.uuid,
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], user_2.name)
        self.assertFalse(response.data['is_owner'])

    def test_get_user_profile_not_exists(self):
        UserProfileFactory(user=self.user, image_portrait='image1.png')

        response = self.client.get('/api/accounts/profile/', {
            'user_uuid': 3,
        })

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_user_profile(self):
        user_profile = UserProfileFactory(user=self.user, nick_name='user 1')

        response = self.client.patch(
            '/api/accounts/profile/', {
                'image_portrait': 'abc.png',
                'name': 'User name 2',
                'nick_name': 'nick_name 2',
                'websites': ['website1', 'website2'],
                'socials': [
                    {
                        'platform': 'facebook',
                        'url': 'https://www.example.com',
                    },
                ],
                'introduction': 'Introduction 1',
                'about_artist': 'About artist 1',
                'membership': [
                    {
                        'year': '2021',
                        'description': 'membership 1',
                    },
                ],
                'training_background': [
                    {
                        'year': '2021',
                        'description': 'training background 1',
                    },
                ],
                'year_of_birth': '2023',
                'place_of_birth': 'HCM',
                'phone_number': '',
            },
            format='json',
        )

        user_profile.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(user_profile.user.name, 'User name 2')
        self.assertEqual(user_profile.nick_name, 'nick_name 2')
        self.assertEqual(user_profile.image_portrait, 'abc.png')
        self.assertEqual(user_profile.websites, ['website1', 'website2'])
        self.assertEqual(user_profile.socials, [{'platform': 'facebook', 'url': 'https://www.example.com'}])
        self.assertEqual(user_profile.introduction, 'Introduction 1')
        self.assertEqual(user_profile.about_artist, 'About artist 1')
        self.assertEqual(user_profile.membership, [{'year': '2021', 'description': 'membership 1'}])
        self.assertEqual(user_profile.training_background, [{'year': '2021', 'description': 'training background 1'}])
        self.assertEqual(user_profile.year_of_birth, '2023')
        self.assertEqual(user_profile.place_of_birth, 'HCM')

    def test_can_update_blank_field(self):
        self.user.name = 'User 1'
        self.user.save()
        user_profile = UserProfileFactory(user=self.user, year_of_birth=2023)

        self.client.patch(
            '/api/accounts/profile/', {
                'name': '',
                'year_of_birth': '',
            },
            format='json',
        )

        user_profile.refresh_from_db()

        self.assertEqual(user_profile.user.name, '')
        self.assertEqual(user_profile.year_of_birth, '')

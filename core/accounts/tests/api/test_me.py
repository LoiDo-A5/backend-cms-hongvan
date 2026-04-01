from faker import Faker
from rest_framework import status
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from core.accounts.factories.user import UserProfileFactory
from core.accounts.tests.api.base_user_test import BaseUserTest


class MeApiTest(BaseUserTest):
    def test_get_me(self):
        UserProfileFactory(user=self.user)
        response = self.client.get('/api/accounts/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('name', response.data)
        self.assertIn('has_usable_password', response.data)

        profile_data = response.data.get('profile', {})
        self.assertIn('nick_name', profile_data)
        self.assertIn('id_card_number', profile_data)
        self.assertIn('address', profile_data)
        self.assertIn('certification', profile_data)
        self.assertIn('introduction', profile_data)

    def test_update_me(self):
        name = Faker().name()
        response = self.client.put(
            '/api/accounts/me/', {
                'name': name,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('name', response.data)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, name)

    def test_update_background(self):
        response = self.client.patch(
            '/api/accounts/me/', {
                'background': 'image_1.png',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertIn('http://testserver', response.data['background'])

    def test_update_avatar(self):
        response = self.client.patch(
            '/api/accounts/me/', {
                'avatar': 'image_1.png',
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertIn('http://testserver', response.data['avatar'])

    def test_update_name(self):
        name = Faker().name()
        response = self.client.patch(
            '/api/accounts/me/', {
                'name': name,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('name', response.data)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, name)
        self.assertEqual(self.user.display_name, name)

    def test_update_birthday(self):
        birthday = Faker().date()
        response = self.client.patch(
            '/api/accounts/me/', {
                'birthday': birthday,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('birthday', response.data)

        self.user.refresh_from_db()
        self.assertEqual(self.user.birthday.strftime('%Y-%m-%d'), birthday)

    def test_delete_account_wrong_password(self):
        self.assertTrue(self.user.is_active)
        response = self.client.delete('/api/accounts/me/', {'password': Faker().name()})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'password': ['The password is invalid']})

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_delete_account_right_password(self):
        password = Faker().name()
        self.user.set_password(password)
        self.user.save()
        self.assertTrue(self.user.is_active)

        response = self.client.delete('/api/accounts/me/', {'password': password})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)

    def test_update_introduction(self):
        introduction = Faker().sentence()
        UserProfileFactory(user=self.user)
        response = self.client.patch(
            '/api/accounts/me/',
            {
                'profile': {
                    'introduction': introduction,
                },
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile_data = response.data.get('profile', {})
        self.assertIn('introduction', profile_data)

        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.introduction, introduction)

    def test_update_birthday_name_and_introduction_nickname(self):
        name = Faker().name()
        nick_name = Faker().user_name()
        introduction = Faker().sentence()
        birthday = Faker().date()
        UserProfileFactory(user=self.user)
        response = self.client.patch(
            '/api/accounts/me/',
            {
                'birthday': birthday,
                'name': name,
                'profile': {
                    'introduction': introduction,
                    'nick_name': nick_name,
                },
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        profile_data = response.data.get('profile', {})
        self.assertIn('introduction', profile_data)
        self.assertIn('nick_name', profile_data)
        self.assertIn('name', response.data)
        self.assertIn('birthday', response.data)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, name)
        self.assertEqual(self.user.birthday.strftime('%Y-%m-%d'), birthday)
        self.assertEqual(self.user.profile.introduction, introduction)
        self.assertEqual(self.user.profile.nick_name, nick_name)

    def test_update_uuid_first_time(self):
        new_uuid = 'new-uuid-first-time'
        self.assertIsNone(self.user.uuid_last_updated_at)

        response = self.client.patch(
            '/api/accounts/me/',
            {'uuid': new_uuid},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.uuid, new_uuid)
        self.assertIsNotNone(self.user.uuid_last_updated_at)

    def test_update_uuid_same_value(self):
        original_uuid = self.user.uuid

        response = self.client.patch(
            '/api/accounts/me/',
            {'uuid': original_uuid},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.uuid, str(original_uuid))

    def test_update_uuid_before_six_months(self):
        self.user.uuid_last_updated_at = timezone.now() - relativedelta(months=3)
        self.user.save()

        new_uuid = 'new-uuid-too-soon'
        response = self.client.patch(
            '/api/accounts/me/',
            {'uuid': new_uuid},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('uuid', response.data)
        self.assertIn('You can edit your public ID again after 6 months.', str(response.data['uuid'][0]))

        self.user.refresh_from_db()
        self.assertNotEqual(self.user.uuid, new_uuid)

    def test_update_uuid_after_six_months(self):
        old_update_time = timezone.now() - relativedelta(months=7)
        self.user.uuid_last_updated_at = old_update_time
        self.user.save()

        new_uuid = 'new-uuid-after-six-months'
        response = self.client.patch(
            '/api/accounts/me/',
            {'uuid': new_uuid},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.uuid, new_uuid)
        self.assertGreater(self.user.uuid_last_updated_at, old_update_time)

    def test_update_uuid_exactly_six_months(self):
        self.user.uuid_last_updated_at = timezone.now() - relativedelta(months=6)
        self.user.save()

        new_uuid = 'new-uuid-exactly-six-months'
        response = self.client.patch(
            '/api/accounts/me/',
            {'uuid': new_uuid},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.uuid, new_uuid)

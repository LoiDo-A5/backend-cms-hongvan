from faker import Faker

from core.accounts.factories.user import UserFactory, UserProfileFactory
from core.accounts.tests.api.base_user_test import BaseUserTest
from rest_framework import status

faker = Faker()


class SearchUserApiTest(BaseUserTest):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

    def test_search_user_by_role(self):
        user_1 = UserFactory(role=1, legal_name='Johnny')
        user_2 = UserFactory(role=2, legal_name='Johnny')
        UserFactory(role=3, legal_name='Johnny')
        UserFactory(role=4, legal_name='Johnny')

        self.user.role = 4
        self.user.save()

        response = self.client.get('/api/accounts/search_user/', {
            'role__in': '1,2',
            'search': 'Johnny',
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['id'], user_1.id)
        self.assertEqual(response.data[1]['id'], user_2.id)

    def test_search_user_by_legal_name(self):
        UserFactory(role=1, legal_name='Johnny')
        UserFactory(role=2, legal_name='Tommy')
        UserFactory(role=3, legal_name='Sammy')

        response = self.client.get('/api/accounts/search_user/', {
            'search': 'john',
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_user_by_nick_name(self):
        user_1 = UserFactory(role=1, legal_name='Johnny')
        UserFactory(role=2, legal_name='Tommy')
        UserFactory(role=3, legal_name='Sammy')

        UserProfileFactory(nick_name='J-man', user=user_1)

        response = self.client.get('/api/accounts/search_user/', {
            'search': 'J-man',
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_search_user_by_phone(self):
        response = self.client.get(f'/api/accounts/search/phone/{self.user.phone_number}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], self.user.name)

    def test_search_user_by_phone_not_exist(self):
        response = self.client.get('/api/accounts/search/phone/0909123456/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_search_user_by_none_query(self):
        UserFactory(role=1, legal_name='Johnny')
        UserFactory(role=2, legal_name='Tommy')
        UserFactory(role=3, legal_name='Sammy')

        response = self.client.get('/api/accounts/search_user/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_search_user_with_empty_search(self):
        UserFactory(role=1, legal_name='Johnny')
        UserFactory(role=2, legal_name='Tommy')
        UserFactory(role=3, legal_name='Sammy')

        response = self.client.get('/api/accounts/search_user/', {
            'search': '',
            'role__in': '1',
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_search_user_with_any_param(self):
        UserFactory(role=1, legal_name='Johnny')
        UserFactory(role=2, legal_name='Tommy')
        UserFactory(role=3, legal_name='Sammy')

        response = self.client.get('/api/accounts/search_user/', {
            'abcd': '',
            'role__in': '1',
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_search_user_exclude(self):
        user_1 = UserFactory(legal_name='Johnny')
        user_2 = UserFactory(legal_name='Johnny')
        user_3 = UserFactory(legal_name='Johnny')

        response = self.client.get('/api/accounts/search_user/', {
            'search': 'Johnny',
            'exclude__in': f'{user_1.id}, {user_2.id}',
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], user_3.id)

    def test_search_user_include_me(self):
        UserFactory(legal_name='Johnny', role=1)
        user_2 = UserFactory(legal_name='Johnny', role=2)
        UserFactory(legal_name='Johnny', role=3)

        self.user.legal_name = 'Johnny'
        self.user.role = 1
        self.user.save()

        response = self.client.get('/api/accounts/search_user/', {
            'search': 'Johnny',
            'role__in': 2,
            'include_me': True,
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['id'], self.user.id)
        self.assertEqual(response.data[1]['id'], user_2.id)

    def test_search_user_params_include_me_should_response_empty_data_if_not_search_params(self):
        UserFactory(legal_name='Johnny', role=1)

        self.user.legal_name = 'Johnny'
        self.user.role = 1
        self.user.save()

        response = self.client.get('/api/accounts/search_user/', {
            'search': '',
            'include_me': True,
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

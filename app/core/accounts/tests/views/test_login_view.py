from django.contrib import auth
from django.contrib.auth.models import AnonymousUser

from common.tests.isolated_cache_test_case import TestCase
from core.accounts.factories.allauth import SiteFactory
from core.accounts.models import User


class LoginViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        SiteFactory(domain='testserver', name='testserver')

    def test_login_view_user_phone_verified(self):
        credentials = {
            'username': 'admin',
            'password': 'admin',
        }
        user = User.objects.create_user(**credentials)
        user.is_phone_verified = True
        user.save()
        self.client.post('/login/', {**credentials, 'remember_me': True})
        user = auth.get_user(self.client)
        self.assertIsInstance(user, User)
        self.assertTrue(user.is_authenticated)

    def test_login_view_user_phone_not_verified(self):
        credentials = {
            'username': 'admin',
            'password': 'admin',
        }
        User.objects.create_user(**credentials)
        self.client.post('/login/', {**credentials, 'remember_me': True})
        user = auth.get_user(self.client)
        self.assertIsInstance(user, AnonymousUser)

    def test_login_view_user_not_check_remember_me(self):
        credentials = {
            'username': 'admin',
            'password': 'admin',
        }
        user = User.objects.create_user(**credentials)
        user.is_phone_verified = True
        user.save()
        self.client.post('/login/', {**credentials, 'remember_me': False})
        self.assertEqual(self.client.session['_session_expiry'], 0)

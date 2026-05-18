from unittest import mock

from django.test import SimpleTestCase

from core.accounts.adapter.custom_social_account_adapter import CustomSocialAccountAdapter


class CustomSocialAccountAdapterLogExceptionTest(SimpleTestCase):
    def test_exception_is_logged_on_auth_error(self):
        exception = Exception()
        request = mock.MagicMock()
        with mock.patch('core.accounts.adapter.custom_social_account_adapter.logger') as logger:
            CustomSocialAccountAdapter().authentication_error(request, 'facebook', exception=exception)

        logger.exception.assert_called_once()
        param = logger.exception.mock_calls[0][1][0]
        self.assertIs(param, exception)

    def test_message_is_logged_on_auth_error(self):
        request = mock.MagicMock()
        with mock.patch('core.accounts.adapter.custom_social_account_adapter.logger') as logger:
            CustomSocialAccountAdapter().authentication_error(request, 'facebook')

        logger.exception.assert_called_once()
        param = logger.exception.mock_calls[0][1][0]
        self.assertEqual(param, 'Fail to login social network')

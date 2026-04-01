from time import time

from rest_framework import status

from core.accounts.tests.api.base_user_test import BaseUserTest
from django_otp.oath import TOTP


# refs: from django_otp.plugins.otp_totp.tests import TOTPDeviceMixin
class TOTPDeviceMixinBase:
    @classmethod
    def setUpTOTPDevice(cls):
        cls.device = cls.user.totpdevice_set.create(
            key='2a2bbba1092ffdd25a328ad1a0a5f5d61d7aacc4', step=30,
            t0=int(time() - (30 * 3)), digits=6, tolerance=0, drift=0,
        )


class TwoFactorVerifyViewTest(BaseUserTest, TOTPDeviceMixinBase):
    @classmethod
    def setUpTestData(cls) -> None:
        super().setUpTestData()
        cls.setUpTOTPDevice()
        cls.totp = TOTP(cls.device.bin_key)

    def test_not_enable_tfa(self):
        self.user.totpdevice_set.all().delete()
        response = self.client.post('/api/accounts/tfa_verify/', {'token': '12345'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'non_field_errors': ['Please enable Two-Factor Authentication first']})

    def test_verify_tfa_authorization_token(self):
        response = self.client.post('/api/accounts/tfa_verify/', {'token': self.totp.token()})
        self.assertResponseStatus(response, status.HTTP_200_OK)

    def test_verify_tfa_authorization_token_invalid_token(self):
        response = self.client.post('/api/accounts/tfa_verify/', {'token': '12345'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'non_field_errors': ['Invalid token']})

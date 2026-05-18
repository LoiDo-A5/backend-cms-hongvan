from django.core.cache import cache
from django.test import SimpleTestCase

from core.accounts.tasks.sms import send_sms


class SendSMSTests(SimpleTestCase):

    def test_send_sms_phone_number_null(self):
        send_sms(None, 'Message')
        self.assertEqual(cache.get('Message'), True)
        send_sms(None, 'Message')
        cache.delete('Message')

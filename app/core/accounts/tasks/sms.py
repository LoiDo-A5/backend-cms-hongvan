import logging

import requests
from celery import shared_task
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


def send_sms(phone, content):
    if not phone:
        if not cache.get(content):
            cache.set(content, True)
        return
    send_sms_real.delay(phone, content)


@shared_task(
    queue='send_sms',
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 5},
)
def send_sms_real(phone, content):
    url = 'http://rest.esms.vn/MainService.svc/json/SendMultipleMessage_V4_get'
    params = {
        'Phone': phone,
        'Content': content,
        'ApiKey': settings.SMS_API_KEY,
        'SecretKey': settings.SMS_SECRET_KEY,
        'IsUnicode': 0,
        'Brandname': 'EoH',
        'SmsType': 2,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()

    res = response.json()
    if res['CodeResult'] == '99':
        logger.warning(f'Invalid phone number {phone} SMS sending failed')
    elif res['CodeResult'] != '100':
        logger.warning(f"Fail to send sms {phone} CodeResult {res['CodeResult']}")
        raise Exception('Fail to send sms')

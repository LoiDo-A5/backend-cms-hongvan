import random
import string
import requests

from django.conf import settings
from django.utils.crypto import get_random_string


def otp_generator():
    return '{:06}'.format(random.randrange(1, 10 ** 6))


def referral_code_generator():
    return get_random_string(length=6, allowed_chars=string.ascii_uppercase + string.digits)


def login_content_generator(otp, timeout):
    minute = int(timeout / 60)
    hash_code = settings.HASH_CODE_AUTO_FILL_SMS
    return f'EoH thong bao ma OTP dang nhap cua ban la: {otp}. Co hieu luc trong {minute} phut. ' \
           f'Vi ly do bao mat, vui long khong chia se ma nay cho bat ky ai. {hash_code}'


def forgot_password_content_generator(otp, timeout):
    minute = int(timeout / 60)
    hash_code = settings.HASH_CODE_AUTO_FILL_SMS
    return f'EoH nhan yeu cau ban quen mat khau ma OTP cua ban la: {otp}. Co hieu luc trong {minute} phut. ' \
           f'Vi ly do bao mat, vui long khong chia se ma nay cho bat ky ai. {hash_code}'


def create_sendbird_user(user_id, nickname, profile_url=None):
    url = f'{settings.SENDBIRD_API_URL}/users'
    headers = {
        'Content-Type': 'application/json',
        'Api-Token': settings.API_TOKEN_SENDBIRD,
    }

    data = {
        'user_id': str(user_id),
        'nickname': nickname,
        'profile_url': profile_url,
    }

    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()

    return response.json()


# def update_sendbird_user(user_id, nickname, profile_url=None):
#     url = f'{settings.SENDBIRD_API_URL}/users/{str(user_id)}'
#     headers = {
#         'Content-Type': 'application/json',
#         'Api-Token': settings.API_TOKEN_SENDBIRD,
#     }
#
#     data = {
#         'nickname': nickname,
#         'profile_url': profile_url,
#     }
#
#     response = requests.put(url, json=data, headers=headers)
#     response.raise_for_status()
#
#     return response.json()

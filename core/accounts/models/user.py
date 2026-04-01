from functools import cached_property

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager
from django.core.cache import cache
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models.manager import BaseManager
from django.utils.crypto import get_random_string

from common.abstract_models.image_field import CustomImageField
from core.accounts.models.permission_list_mixin import PermissionListMixin
from core.accounts.tasks.notification import send_one_signal_notification
from core.accounts.tasks.sms import send_sms
from core.accounts.utils import forgot_password_content_generator
from core.accounts.utils import login_content_generator
from core.accounts.utils import otp_generator
from core.accounts.utils import referral_code_generator
import uuid


class USER_ROLE:
    USER = 1
    STAFF = 2


USER_ROLE_CHOICES = (
    (USER_ROLE.USER, 'User'),
    (USER_ROLE.STAFF, 'Staff'),
)


class UserQuerySet(models.QuerySet):
    pass


class CustomUserManager(BaseManager.from_queryset(UserQuerySet), UserManager):
    pass


class User(AbstractUser, PermissionListMixin):
    phone_number = models.CharField(max_length=50, null=True)
    name = models.CharField(max_length=80, blank=True, null=True)
    email = models.EmailField(null=True, blank=True)
    is_using_social_avatar = models.BooleanField(default=False)
    social_avatar_hash = models.CharField(max_length=32, default='')
    avatar = CustomImageField(blank=True)
    background = CustomImageField(blank=True)
    birthday = models.DateField(null=True, blank=True)
    is_phone_verified = models.BooleanField(default=False)
    time_zone = models.CharField(max_length=50, default='Asia/Ho_Chi_Minh', blank=True)
    last_seen_notification_at = models.DateTimeField(null=True, blank=True)
    role = models.IntegerField(
        choices=USER_ROLE_CHOICES,
        blank=True,
        null=True,
    )
    gender = models.IntegerField(
        choices=[(0, 'Male'), (1, 'Female')],
        default=0,
    )
    language = models.CharField(
        choices=[('en', 'English'), ('vi', 'Tiếng Việt')],
        default='en',
        max_length=50,
    )

    referral_code = models.CharField(
        max_length=6, unique=True, default=referral_code_generator,
        validators=[MinLengthValidator(6)],
    )
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    has_activated = models.BooleanField(default=False)
    legal_name = models.CharField(max_length=80, blank=True, null=True)
    year_of_birth = models.CharField(null=True, blank=True)
    place_of_birth = models.CharField(null=True, blank=True)

    uuid = models.CharField(default=uuid.uuid4, unique=True, error_messages={'unique': 'Public ID already in use.'})
    uuid_last_updated_at = models.DateTimeField(null=True, blank=True)

    is_first_login = models.BooleanField(default=True)

    objects = CustomUserManager()

    def __str__(self):  # pragma: nocover
        return f'{self.username} | {self.name} | {self.phone_number} | {self.email}'

    @property
    def register_otp_key(self):
        return cache.get(f'register_opt_{self.id}')

    @property
    def forgot_password_key(self):
        return f'{self.id}_forgot_password_data'

    def verify_register_opt(self, otp):
        return cache.get(self.register_otp_key)['code'] == otp

    def send_register_otp(self):
        otp = otp_generator()
        key = get_random_string(32)
        cache.set(f'register_opt_{self.id}', key, settings.SMS_OPT_TIMEOUT)
        cache.set(
            key, {
                'code': otp,
                'user_id': self.id,
            }, settings.SMS_OPT_TIMEOUT,
        )
        send_sms(self.phone_number, login_content_generator(otp, settings.SMS_OPT_TIMEOUT))

    @property
    def forgot_password_data(self):
        return cache.get(self.forgot_password_key) or {'otp': '', 'is_verified': False}

    @cached_property
    def display_name(self):
        return self.name or self.email or self.username

    def set_forgot_password_data(self, value):
        cache.set(self.forgot_password_key, value, settings.SMS_OPT_TIMEOUT)

    def send_forgot_password_otp(self):
        otp = otp_generator()
        self.set_forgot_password_data({'otp': otp, 'is_verified': False})
        send_sms(self.phone_number, forgot_password_content_generator(otp, settings.SMS_OPT_TIMEOUT))

    def send_notification(self, title, message, credentials=None, **options):
        send_one_signal_notification.delay(
            user_id=self.id,
            title=title,
            message=message,
            credentials=credentials,
            **options,
        )

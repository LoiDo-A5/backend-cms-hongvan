from django.conf import settings
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework import status
from rest_framework import throttling
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from common.api.ignore_throttle_on_test import IgnoreThrottleOnTestMixin
from core.accounts.api.user_api import UserSerializer
from core.accounts.models import User
from core.accounts.utils import create_sendbird_user
import requests


class RegisterPhoneSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(min_length=10, max_length=15, source='phone_number')
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    referred_by = serializers.SlugRelatedField(
        slug_field='referral_code',
        queryset=User.objects.all(),
        required=False, allow_null=True,
        error_messages={
            'does_not_exist': _('Invalid referral code, please check again.'),
        },
    )

    class Meta:
        model = User
        fields = (
            'phone',
            'email',
            'password1',
            'password2',
            'time_zone',
            'referred_by',
            'role',
        )

    def validate_phone(self, phone):
        if not phone.isdigit():
            raise serializers.ValidationError(gettext('Phone number must only contain digits'))
        return phone

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if attrs['password1'] != attrs['password2']:
            raise serializers.ValidationError(gettext("The two password fields didn't match."))

        attrs['password'] = attrs.pop('password1')
        attrs.pop('password2')

        phone = attrs['phone_number']
        email = attrs['email']
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({
                'email': 'Email address already in use',
            })

        if User.objects.filter(phone_number=phone).exists():
            user = User.objects.get(phone_number=phone)
            if not user.is_phone_verified:
                raise serializers.ValidationError(
                    {
                        'phone': {
                            'message': gettext(
                                'The phone number is registered but not verified. Please verify phone number',
                            ),
                            'code': 'phone_need_verify',
                            'user_id': user.id,
                            'phone': user.phone_number,
                            'key': user.register_otp_key,
                        },
                    },
                    code='phone_need_verify',
                )

            raise serializers.ValidationError(
                gettext(
                    "There's an account associated with this phone number. "
                    "If that's yours, please go back to Forgot password to set a new one.",
                ),
            )

        attrs['username'] = attrs['phone_number']

        return attrs

    def validate_time_zone(self, time_zone):
        if not time_zone:
            time_zone = 'Asia/Ho_Chi_Minh'
        return time_zone

    def process_register_member(self):
        user = User(
            is_active=True,
            is_phone_verified=False,
            **self.validated_data,
        )
        user.set_password(self.validated_data['password'])
        user.save()

        try:
            create_sendbird_user(user.uuid, user.name, None)
        except requests.exceptions.RequestException:
            raise serializers.ValidationError({
                'sendbird': 'Failed to create Sendbird user. Please try again later.',
            })

        return user, None


class RegisterByPhoneThrottle(throttling.AnonRateThrottle):
    def get_rate(self):
        return settings.THROTTLE_RATES_USER_REGISTER


class RegisterPhoneApi(IgnoreThrottleOnTestMixin, GenericAPIView):
    serializer_class = RegisterPhoneSerializer
    throttle_classes = [RegisterByPhoneThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user, _ = serializer.process_register_member()
        user.send_register_otp()

        return Response(
            {
                'message': gettext('Sent OTP code'),
                'key': user.register_otp_key,
                'user': UserSerializer(user).data,
            }, status.HTTP_200_OK,
        )

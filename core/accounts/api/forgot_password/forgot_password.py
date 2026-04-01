from django.utils.translation import gettext
from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.throttling import SimpleRateThrottle

from core.accounts.models import User


class UserSendOtpThrottle(SimpleRateThrottle):
    scope = 'user_send_otp'

    def get_cache_key(self, request, view):
        phone = request.data.get('username')  # forgot password
        if not phone:
            phone = request.data.get('phone')  # sign up and resend register
        ident = f'{phone}' if phone else self.get_ident(request)

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident,
        }


class ForgotPasswordSerializer(serializers.Serializer):
    username = serializers.CharField()

    def validate(self, attrs):
        try:
            user = User.objects.get(username=attrs['username'])
        except User.DoesNotExist:
            raise serializers.ValidationError(gettext('Account does not exist'))
        attrs['user'] = user
        return attrs


class ForgotPasswordApi(GenericAPIView):
    serializer_class = ForgotPasswordSerializer
    throttle_classes = [UserSendOtpThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        user.send_forgot_password_otp()
        return Response(status=HTTP_200_OK)

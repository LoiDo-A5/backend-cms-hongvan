from django.utils.translation import gettext
from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from core.accounts.api.forgot_password.forgot_password import ForgotPasswordSerializer


class ForgotPasswordVerifyOtpSerializer(ForgotPasswordSerializer):
    forgot_password_otp = serializers.CharField(min_length=6, max_length=6)

    def validate(self, attrs):
        data = super(ForgotPasswordVerifyOtpSerializer, self).validate(attrs)
        user = data['user']
        if user.forgot_password_data['is_verified']:
            raise serializers.ValidationError(gettext('Your OTP has been verified'))
        if not user.forgot_password_data['otp']:
            raise serializers.ValidationError(gettext('You have not requested to forgot password'))

        forgot_password_otp = attrs['forgot_password_otp']
        if forgot_password_otp != user.forgot_password_data['otp']:
            raise serializers.ValidationError({'forgot_password_otp': ['Incorrect OTP']})
        attrs['user'] = user
        return attrs


class ForgotPasswordVerifyOtpApi(GenericAPIView):
    serializer_class = ForgotPasswordVerifyOtpSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        user.set_forgot_password_data({'otp': '', 'is_verified': True})
        return Response(status=HTTP_200_OK)

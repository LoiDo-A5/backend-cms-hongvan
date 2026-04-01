from django.utils.translation import gettext
from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK

from core.accounts.api.forgot_password.forgot_password import ForgotPasswordSerializer


class ForgotPasswordSetPasswordSerializer(ForgotPasswordSerializer):
    password = serializers.CharField()

    def validate(self, attrs):
        data = super(ForgotPasswordSetPasswordSerializer, self).validate(attrs)
        user = data['user']
        if not user.forgot_password_data['is_verified']:
            raise serializers.ValidationError(gettext('Please verify OTP first'))
        if user.forgot_password_data['otp']:
            raise serializers.ValidationError(gettext('Verified but OTP is not valid'))

        return attrs


class ForgotPasswordSetPasswordApi(GenericAPIView):
    serializer_class = ForgotPasswordSetPasswordSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        password = serializer.validated_data['password']

        user.set_forgot_password_data({'otp': '', 'is_verified': False})
        user.set_password(password)
        user.is_active = True
        user.save()

        return Response(status=HTTP_200_OK)

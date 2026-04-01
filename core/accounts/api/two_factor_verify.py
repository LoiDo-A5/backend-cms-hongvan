from django.utils.translation import gettext as _
from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django_otp.oath import TOTP
from django_otp.plugins.otp_totp.models import TOTPDevice
from two_factor.utils import totp_digits


class TFAVerifyViewSerializer(serializers.Serializer):
    token = serializers.IntegerField(min_value=1, max_value=int('9' * totp_digits()))

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.context['request'].user
        try:
            # Note: change when implement SMS/call methods
            device = user.totpdevice_set.get()
        except TOTPDevice.DoesNotExist:
            raise serializers.ValidationError(_('Please enable Two-Factor Authentication first'))

        totp = TOTP(device.bin_key)
        is_verified = totp.verify(data['token'])
        if not is_verified:
            raise serializers.ValidationError(_('Invalid token'))
        return data


class TFAVerifyView(GenericAPIView):
    serializer_class = TFAVerifyViewSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response()

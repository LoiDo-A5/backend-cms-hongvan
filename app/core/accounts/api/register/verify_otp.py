from django.core.cache import cache
from django.utils.translation import gettext
from rest_framework import serializers
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.generics import GenericAPIView
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.throttling import SimpleRateThrottle

from core.accounts.api.user_api import UserSerializer
from core.accounts.models import User


class UserVerifyOtpThrottle(SimpleRateThrottle):
    scope = 'user_verify_otp'

    def get_cache_key(self, request, view):
        phone = request.data.get('phone')
        ident = f'{phone}' if phone else self.get_ident(request)
        return self.cache_format % {
            'scope': self.scope,
            'ident': ident,
        }


class OtpSerializer(serializers.Serializer):
    otp_key = serializers.CharField(min_length=32, max_length=32)
    code = serializers.CharField(min_length=6, max_length=6)

    def validate(self, attrs):
        data = super().validate(attrs)
        value = cache.get(data['otp_key'])
        if not value:
            raise serializers.ValidationError(gettext('Invalid OTP key'))

        user_id = value['user_id']
        user = get_object_or_404(User, pk=user_id)
        if user.is_phone_verified:
            raise serializers.ValidationError(gettext("User's phone number was already verified"))
        data['user'] = user
        return data


class VerifyOtpApi(GenericAPIView):
    serializer_class = OtpSerializer
    throttle_classes = [UserVerifyOtpThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['code']
        user = serializer.validated_data['user']

        if not user.verify_register_opt(code):
            return Response({'message': gettext('Invalid OTP')}, status.HTTP_400_BAD_REQUEST)

        user.is_phone_verified = True
        user.save()
        token = Token.objects.create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
        })

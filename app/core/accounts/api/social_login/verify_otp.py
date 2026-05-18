from django.core.cache import cache
from django.utils.translation import gettext
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from core.accounts.api.social_login.send_otp import SocialSendOtpSerializer
from core.accounts.api.user_api import UserSerializer
from core.accounts.models import User


class SocialVerifyOtpSerializer(SocialSendOtpSerializer):
    otp = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):
        attrs = super(SocialVerifyOtpSerializer, self).validate(attrs)
        phone = attrs['phone']
        user = attrs['user']
        otp = attrs['otp']
        value = cache.get(f'{user.id}_social_login_otp')
        if not value:
            raise serializers.ValidationError(gettext('You have not requested to verify yet.'))
        if value['phone'] != phone or value['otp'] != otp:
            raise serializers.ValidationError(gettext('Invalid OTP.'))

        self.instance = user
        return attrs

    def update(self, instance, validated_data):
        phone = validated_data['phone']
        if User.objects.filter(phone_number=phone).exists():
            user = User.objects.get(phone_number=phone)
            instance.socialaccount_set.update(user=user)
            instance.delete()
            instance = user
        else:
            instance.phone_number = phone
            cache.delete(f'{instance.id}_social_login_otp')
        instance.is_active = validated_data['is_active']
        instance.save()
        return instance


class SocialVerifyOtpApi(GenericAPIView):
    serializer_class = SocialVerifyOtpSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save(is_active=True)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
        })

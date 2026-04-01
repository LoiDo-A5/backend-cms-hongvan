from django.core.cache import cache
from django.utils.translation import gettext
from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from core.accounts.api.forgot_password.forgot_password import UserSendOtpThrottle
from core.accounts.models import User
from core.accounts.tasks.sms import send_sms
from core.accounts.utils import login_content_generator
from core.accounts.utils import otp_generator
from root import settings


class SocialSendOtpSerializer(serializers.Serializer):
    phone = serializers.CharField(min_length=10, max_length=15)
    user = serializers.IntegerField()

    def validate_user(self, user):
        user = get_object_or_404(User, pk=user)
        if not user.socialaccount_set.all():
            raise serializers.ValidationError(gettext('This user is not registered by social.'))
        return user


class SocialSendOtpApi(GenericAPIView):
    serializer_class = SocialSendOtpSerializer
    throttle_classes = [UserSendOtpThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']
        user = serializer.validated_data['user']
        otp = otp_generator()
        cache.set(f'{user.id}_social_login_otp', {'otp': otp, 'phone': phone}, settings.SMS_OPT_TIMEOUT)
        send_sms(phone, login_content_generator(otp, settings.SMS_OPT_TIMEOUT))
        return Response({'message': 'ok'})

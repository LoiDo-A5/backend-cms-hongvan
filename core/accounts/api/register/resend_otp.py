from django.core.cache import cache
from django.utils.translation import gettext_lazy
from rest_framework import serializers
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response

from core.accounts.api.forgot_password.forgot_password import UserSendOtpThrottle
from core.accounts.models import User


class ResendOtpSerializer(serializers.Serializer):
    key = serializers.CharField()


class ResendOtpApi(GenericAPIView):
    serializer_class = ResendOtpSerializer
    throttle_classes = [UserSendOtpThrottle]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp_value = cache.get(serializer.validated_data['key'])
        if not otp_value:
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        user_id = otp_value['user_id']
        try:
            user = User.objects.get(id=user_id)
            user.send_register_otp()
        except User.DoesNotExist:
            pass
        return Response({'message': gettext_lazy('OTP is sent if existing in the system')})

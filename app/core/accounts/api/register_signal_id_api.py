from rest_framework import (
    serializers,
    status,
)
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.accounts.models import UserSignalId


class SignalIdSerializer(serializers.Serializer):
    signal_id = serializers.UUIDField()

    def create(self, validated_data):
        signal_id = validated_data['signal_id']
        signal = UserSignalId.objects.filter(signal_id=signal_id).first()
        user = self.context['request'].user

        if signal:
            if signal.user_id == user.id:
                return signal

            signal.delete()
        signal = UserSignalId.objects.create(signal_id=signal_id, user=user)

        return signal


class RegisterSignalIdApi(GenericAPIView):
    serializer_class = SignalIdSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(status=status.HTTP_201_CREATED)

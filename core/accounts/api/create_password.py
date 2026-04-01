from django.utils.translation import gettext
from rest_framework import serializers
from rest_framework import status
from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.accounts.models import User


class CreatePasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)
    confirm_password = serializers.CharField(required=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError(gettext('Your confirm password is wrong'))
        return attrs

    def process(self):
        user = self.context['request'].user
        new_password = self.validated_data['new_password']
        user.set_password(new_password)
        user.save()


class CreatePasswordApi(UpdateAPIView):
    model = User
    serializer_class = CreatePasswordSerializer
    permission_classes = (IsAuthenticated,)

    def update(self, request, *args, **kwargs):
        if request.user.has_usable_password():
            return Response(
                {'message': gettext('Not allowed to create new password')},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.process()
        return Response(data={'message': gettext('Password created successfully')})

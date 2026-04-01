from django.utils.translation import gettext
from rest_framework import serializers
from rest_framework.response import Response

from core.accounts.api.create_password import CreatePasswordApi
from core.accounts.api.create_password import CreatePasswordSerializer


class ChangePasswordSerializer(CreatePasswordSerializer):
    old_password = serializers.CharField(required=True)

    def validate_old_password(self, old_password):
        user = self.context['request'].user
        if not user.check_password(old_password):
            raise serializers.ValidationError(gettext('Your old password is wrong'))
        return old_password

    def validate(self, attrs):
        data = super().validate(attrs)
        if attrs['new_password'] == attrs['old_password']:
            raise serializers.ValidationError(gettext('Your new password cannot be the same as your old password'))
        return data


class ChangePasswordApi(CreatePasswordApi):
    serializer_class = ChangePasswordSerializer

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.process()
        user = request.user
        if user.is_first_login:
            user.is_first_login = False
            user.save(update_fields=['is_first_login'])
        return Response(data={'message': gettext('Password updated successfully')})

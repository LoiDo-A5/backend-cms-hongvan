from rest_framework import serializers
from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from dateutil.relativedelta import relativedelta

from core.accounts.api.user_api import UserSerializer, ArtistProfilePatchSerializer
from core.accounts.models import User, UserProfile


class MeSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField()

    def update(self, instance, validated_data):
        user = instance
        user.name = validated_data['name']
        user.save()
        return user


class MePatchSerializer(serializers.ModelSerializer):
    profile = ArtistProfilePatchSerializer()
    avatar = serializers.CharField()
    background = serializers.CharField()

    class Meta:
        model = User
        fields = (
            'id',
            'name',
            'email',
            'avatar',
            'background',
            'phone_number',
            'birthday',
            'referral_code',
            'display_name',
            'profile',
            'role',
            'legal_name',
            'year_of_birth',
            'place_of_birth',
            'uuid',
        )
        read_only_fields = (
            'referral_code',
        )

    def validate_uuid(self, value):
        if value == self.instance.uuid:
            return value

        if self.instance.uuid_last_updated_at is None:
            return value

        six_months_ago = timezone.now() - relativedelta(months=6)
        if self.instance.uuid_last_updated_at > six_months_ago:
            raise serializers.ValidationError('You can edit your Gladius ID again after 6 months.')

        return value

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)

        if profile_data:
            UserProfile.objects.update_or_create(
                user=instance,
                defaults={**profile_data})

        old_uuid = instance.uuid
        uuid_changed = 'uuid' in validated_data and validated_data['uuid'] != old_uuid
        if uuid_changed:
            instance.uuid_last_updated_at = timezone.now()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.is_first_login = False
        instance.save()

        if uuid_changed:
            from activity_log.models.user_log import UserLog, USER_ACTION_UPDATE_GLADIUS_ID
            UserLog.objects.create(
                user=instance,
                action_type=USER_ACTION_UPDATE_GLADIUS_ID,
                content_vi=f'Người dùng thay đổi Gladius ID từ {old_uuid} sang {instance.uuid}',
                content_en=f'User changed Gladius ID from {old_uuid} to {instance.uuid}',
                params={
                    'previous_uuid': old_uuid,
                    'new_uuid': instance.uuid,
                },
            )
        return instance


class UserPasswordSerializer(serializers.Serializer):
    password = serializers.CharField()

    def validate_password(self, value):
        data = super(UserPasswordSerializer, self).validate(value)
        if not self.context['request'].user.check_password(data):
            raise serializers.ValidationError('The password is invalid')
        return data


class MeApi(GenericAPIView):
    serializer_class = MeSerializer
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return UserSerializer
        if self.request.method == 'PATCH':
            return MePatchSerializer
        if self.request.method == 'DELETE':
            return UserPasswordSerializer
        return super().get_serializer_class()

    def get(self, request):
        serializer = self.get_serializer(instance=request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = self.get_serializer(instance=request.user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def patch(self, request):
        serializer = self.get_serializer(instance=request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        context = self.get_serializer_context()
        response_serializer = UserSerializer(request.user, context=context)
        return Response(response_serializer.data)

    def delete(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        request.user.is_active = False
        request.user.save()

        return Response(status=status.HTTP_204_NO_CONTENT)

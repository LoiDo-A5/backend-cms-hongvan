from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.generics import get_object_or_404

from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from core.accounts.models import UserProfile
from core.accounts.models import User
from core.accounts.models.user import USER_ROLE_CHOICES


class UserProfileSerializer(serializers.ModelSerializer):
    legal_name = serializers.CharField(source='user.legal_name', required=False, allow_blank=True)
    name = serializers.CharField(source='user.name', required=False, allow_blank=True)
    is_owner = serializers.BooleanField(read_only=True)
    avatar = serializers.ImageField(source='user.avatar', required=False, allow_null=True)
    role = serializers.ChoiceField(source='user.role', choices=USER_ROLE_CHOICES)
    background = serializers.ImageField(source='user.background', required=False, allow_null=True)
    uuid_user = serializers.CharField(source='user.uuid', required=False, allow_blank=True)
    year_of_birth = serializers.CharField(source='user.year_of_birth', required=False, allow_blank=True)
    place_of_birth = serializers.CharField(source='user.place_of_birth', required=False, allow_blank=True)

    class Meta:
        model = UserProfile
        fields = (
            'id',
            'name',
            'nick_name',
            'email',
            'phone_number',
            'address',
            'live_at',
            'image_portrait',
            'bio',
            'year_of_birth',
            'place_of_birth',
            'is_owner',
            'avatar',
            'role',
            'background',
            'legal_name',
            'uuid_user',
        )
        ref_name = 'UserProfileSerializer'

    def to_representation(self, instance):
        user = self.context['request'].user
        instance.is_owner = instance.has_owner(user)
        return super().to_representation(instance)


class UserProfilePatchSerializer(UserProfileSerializer):
    image_portrait = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = UserProfile
        fields = UserProfileSerializer.Meta.fields + ('image_portrait',)
        ref_name = 'UserProfilePatchSerializer'

    def update(self, instance, validated_data):
        user_instance = instance.user
        user_data = validated_data.pop('user', {})
        for attr, value in user_data.items():
            setattr(user_instance, attr, value)
        user_instance.save()

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class UserProfileApi(GenericAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return UserProfilePatchSerializer
        return super().get_serializer_class()

    def get(self, request):
        user_uuid = request.query_params.get('user_uuid')
        user = get_object_or_404(User, uuid=user_uuid) if user_uuid else request.user

        user_profile, _ = UserProfile.objects.get_or_create(user=user)
        serializer = self.get_serializer(instance=user_profile)
        return Response(serializer.data)

    def patch(self, request):
        user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(instance=user_profile, data=request.data, partial=True)

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

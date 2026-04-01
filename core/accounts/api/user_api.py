from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.mixins import RetrieveModelMixin

from core.accounts.models import User
from core.accounts.models import UserProfile


class ArtistProfilePatchSerializer(serializers.ModelSerializer):
    image_portrait = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = UserProfile
        fields = ('nick_name', 'id_card_number', 'address', 'certification', 'introduction', 'place_of_birth',
                  'year_of_birth', 'live_at', 'email', 'websites', 'socials', 'phone_number', 'image_portrait')


class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserProfile
        fields = ('nick_name', 'id_card_number', 'address', 'certification', 'introduction', 'place_of_birth',
                  'year_of_birth', 'live_at', 'email', 'websites', 'socials', 'phone_number', 'image_portrait')


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'uuid',
            'name',
            'role',
            'email',
            'is_using_social_avatar',
            'social_avatar_hash',
            'avatar',
            'background',
            'phone_number',
            'birthday',
            'has_usable_password',
            'profile',
            'has_activated',
            'legal_name',
            'year_of_birth',
            'place_of_birth',
            'is_first_login',
        )


class SearchUserByPhoneApi(GenericAPIView, RetrieveModelMixin):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = 'phone_number'

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

from rest_framework import serializers

from artwork.models import ArtWork
from artwork.models import ImageArtwork
from core.accounts.models import User


class ArtistArtWorkSerializer(serializers.ModelSerializer):
    nick_name = serializers.CharField(source='profile.nick_name')
    avatar = serializers.ImageField(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'uuid', 'name', 'nick_name', 'avatar', 'phone_number', 'email', 'legal_name']


class ArtistSerializer(serializers.ModelSerializer):
    first_artwork_images = serializers.ImageField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'uuid', 'role', 'name', 'first_artwork_images', 'legal_name', 'avatar', 'background')
        ref_name = 'ArtistSerializerRef'

    def to_representation(self, instance):
        artwork = ArtWork.objects.filter(artist=instance, is_public=True).first()
        images = ImageArtwork.objects.filter(artwork=artwork)

        if images.exists():
            first_image = images[0].image
        else:
            first_image = None

        instance.first_artwork_images = first_image
        return super().to_representation(instance)

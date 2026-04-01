from rest_framework import serializers

from core.accounts.models import UserAward
from core.accounts.models import ImageAward
from django.utils.translation import gettext

from core.accounts.serializers.artist import ArtistArtWorkSerializer


class AwardCreateSerializer(serializers.ModelSerializer):
    images = serializers.ListField(write_only=True, child=serializers.CharField())
    year = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = UserAward
        fields = ('year', 'description', 'is_public', 'images')

    def validate(self, attrs):
        if len(attrs['images']) > 5:
            raise serializers.ValidationError(gettext('Maximum 5 images are allowed.'))
        return attrs

    def create_image_award(self, award, images):
        image_objects = [ImageAward(award=award, image=image) for image in images]
        ImageAward.objects.bulk_create(image_objects)

    def create(self, validated_data):
        user = self.context['request'].user
        images = validated_data.pop('images', None)

        award = UserAward.objects.create(user=user, **validated_data)
        self.create_image_award(award, images)

        return award


class AwardSerializer(serializers.ModelSerializer):
    images = serializers.ListField(read_only=True, child=serializers.ImageField())
    user = ArtistArtWorkSerializer()

    class Meta:
        model = UserAward
        fields = ('id', 'user', 'year', 'description', 'is_public', 'images')

    def to_representation(self, instance):
        images = ImageAward.objects.filter(award=instance)
        instance.images = [item.image for item in images]

        return super().to_representation(instance)


class ImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField()
    key_images = serializers.CharField(source='image')

    class Meta:
        model = ImageAward
        fields = ('image', 'key_images')


class AwardListSerializer(serializers.ModelSerializer):
    list_image = ImageSerializer(many=True, read_only=True)
    user = ArtistArtWorkSerializer()

    class Meta:
        model = UserAward
        fields = ('id', 'user', 'year', 'description', 'is_public', 'list_image')

    def to_representation(self, instance):
        images = ImageAward.objects.filter(award=instance)
        instance.list_image = images
        representation = super().to_representation(instance)
        return representation


class AwardPatchSerializer(serializers.ModelSerializer):
    images = serializers.ListField(write_only=True, child=serializers.CharField(), required=False)

    class Meta:
        model = UserAward
        fields = ('year', 'description', 'is_public', 'images')

    def validate(self, attrs):
        if len(attrs.get('images', [])) > 5:
            raise serializers.ValidationError(gettext('Maximum 5 images are allowed.'))
        return attrs

    def update(self, instance, validated_data):
        instance.year = validated_data.get('year', instance.year)
        instance.description = validated_data.get('description', instance.description)
        instance.is_public = validated_data.get('is_public', instance.is_public)

        images = validated_data.get('images')
        self.update_images(instance, images)
        instance.save()
        return instance

    def update_images(self, instance, images):
        existing_images = ImageAward.objects.filter(award=instance)
        existing_filenames = [image.image for image in existing_images]

        if not images:
            existing_images.delete()
        else:
            for image in images:
                if image not in existing_filenames:
                    ImageAward.objects.create(award=instance, image=image)
            ImageAward.objects.filter(award=instance, image__in=existing_filenames).exclude(image__in=images).delete()

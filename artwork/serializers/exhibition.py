from rest_framework import serializers
from artwork.models import Exhibition, ExhibitionGroup, ArtWork
from artwork.utils.const import EXHIBITION_TYPE_CHOICES
from core.accounts.api.user_api import UserSerializer
from common.serializers.common import ChoiceFieldSerializer
from artwork.serializers.artwork import ArtworkSerializer


class ExhibitionGroupSerializer(serializers.ModelSerializer):
    artworks = serializers.PrimaryKeyRelatedField(queryset=ArtWork.objects.all(), many=True)
    id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = ExhibitionGroup
        fields = ('id', 'title', 'description', 'artworks')


class ExhibitionCreateSerializer(serializers.ModelSerializer):
    cover_image = serializers.CharField(required=False)
    groups = ExhibitionGroupSerializer(many=True)

    class Meta:
        model = Exhibition
        fields = [
            'id',
            'title',
            'date_start',
            'date_end',
            'address',
            'event_type',
            'cover_image',
            'preface',
            'organizer_name',
            'is_public',
            'is_draft',
            'groups',
            'curator',
        ]

    def create(self, validated_data):
        user = self.context['request'].user
        groups = validated_data.pop('groups')
        exhibition = Exhibition.objects.create(**validated_data, owner=user)

        for group_data in groups:
            artworks = group_data.pop('artworks')
            exhibition_group = ExhibitionGroup.objects.create(exhibition=exhibition, **group_data)
            exhibition_group.artworks.set(artworks)

        return exhibition


class ExhibitionGroupReadSerializer(serializers.ModelSerializer):
    artworks = serializers.PrimaryKeyRelatedField(queryset=ArtWork.objects.all(), many=True)
    artwork_links = serializers.SerializerMethodField()

    class Meta:
        model = ExhibitionGroup
        fields = ('id', 'title', 'description', 'artworks', 'artwork_links')

    def get_artwork_links(self, instance):
        artworks = instance.artworks.all()
        return ArtworkSerializer(artworks, many=True, context=self.context).data


class ExhibitionSerializer(serializers.ModelSerializer):
    owner = UserSerializer()
    is_owner = serializers.BooleanField(read_only=True)
    event_type = ChoiceFieldSerializer(choices=EXHIBITION_TYPE_CHOICES)
    groups = ExhibitionGroupReadSerializer(many=True, read_only=True)
    is_ongoing = serializers.BooleanField(read_only=True)

    class Meta:
        model = Exhibition
        fields = [
            'id',
            'title',
            'date_start',
            'date_end',
            'address',
            'event_type',
            'cover_image',
            'preface',
            'organizer_name',
            'is_public',
            'is_draft',
            'owner',
            'is_owner',
            'groups',
            'is_ongoing',
            'curator',
        ]

    def to_representation(self, instance):
        user = self.context['request'].user
        instance.is_owner = instance.has_owner(user)
        instance.is_ongoing = instance.has_ongoing()
        return super().to_representation(instance)


class ExhibitionSaveAsDraftSerializer(serializers.ModelSerializer):
    cover_image = serializers.CharField(required=False)

    class Meta:
        model = Exhibition
        fields = [
            'id',
            'title',
            'date_start',
            'date_end',
            'address',
            'event_type',
            'cover_image',
            'preface',
            'organizer_name',
            'is_public',
            'is_draft',
            'owner',
        ]


class ExhibitionUpdateSerializer(serializers.ModelSerializer):
    cover_image = serializers.CharField(required=False)
    groups = ExhibitionGroupSerializer(many=True, required=False)

    class Meta:
        model = Exhibition
        fields = [
            'id',
            'title',
            'date_start',
            'date_end',
            'address',
            'event_type',
            'cover_image',
            'preface',
            'organizer_name',
            'is_public',
            'is_draft',
            'groups',
        ]

    def update(self, instance, validated_data):
        groups_data = validated_data.pop('groups', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        existing_group_ids = []

        if groups_data:
            for group_data in groups_data:
                artworks = group_data.pop('artworks', [])
                group_id = group_data.get('id', None)
                group_data.pop('artwork_links', [])

                exhibition_group, created = ExhibitionGroup.objects.update_or_create(
                    id=group_id, exhibition=instance, defaults=group_data,
                )

                exhibition_group.artworks.set(artworks)
                existing_group_ids.append(exhibition_group.id)

            instance.groups.exclude(id__in=existing_group_ids).delete()

        return instance

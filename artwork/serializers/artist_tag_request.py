from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from artwork.models import ArtistTagRequest, ArtWork, ArtworkEdition, ImageArtwork
from artwork.serializers.artwork import SizeArtworkSerializer, MediumSerializer, StyleSerializer, SubjectSerializer
from artwork.serializers.artwork_certificate import LinkedArtworkSerializer
from artwork.serializers.artwork import ArtworkArtistSerializer
from artwork.serializers.artwork import GetArtistTagRequestSerializer
from artwork.utils.artwork import copy_artwork, generate_artwork_edition
from artwork.utils.const import STATUS_REQUEST, CATEGORY_CHOICES
from common.serializers.common import ChoiceFieldSerializer
from core.accounts.api.user_api import UserSerializer
from core.accounts.models import User


class EditionReviewSerializer(serializers.ModelSerializer):

    class Meta:
        model = ArtworkEdition
        fields = ('id', 'edition_number')


class ArtworkReviewDataSerializer(serializers.ModelSerializer):
    category = ChoiceFieldSerializer(choices=CATEGORY_CHOICES)
    size = SizeArtworkSerializer()
    medium = MediumSerializer()
    image = serializers.ImageField(read_only=True)
    style = StyleSerializer(required=False, allow_null=True)
    subject = SubjectSerializer(required=False, allow_null=True)
    images = serializers.ListField(read_only=True, child=serializers.ImageField())
    editions = EditionReviewSerializer(read_only=True, many=True, source='list_editions')
    linked_artwork = LinkedArtworkSerializer()
    artist_artwork = ArtworkArtistSerializer()
    artist_tag_request = GetArtistTagRequestSerializer()

    class Meta:
        model = ArtWork
        fields = (
            'id',
            'title',
            'owner',
            'title',
            'total_edition',
            'year_created',
            'period_created',
            'size',
            'medium',
            'image',
            'category',
            'currency',
            'total_edition',
            'style',
            'subject',
            'orientation',
            'description',
            'images',
            'total_edition',
            'editions',
            'linked_artwork',
            'artist_artwork',
            'artist_tag_request',
        )

    def to_representation(self, instance):
        images = ImageArtwork.objects.filter(artwork=instance)
        instance.image = images.first().image if images.exists() else None
        instance.images = [item.image for item in images]
        instance.list_editions = instance.editions.all().order_by('edition_number')

        instance.artist_tag_request = instance.tag_request.filter(status__in=[
            STATUS_REQUEST.REQUEST_RECEIVED,
            STATUS_REQUEST.REQUEST_APPROVED,
            STATUS_REQUEST.REQUEST_DENIED,
        ]).first()
        return super().to_representation(instance)


class UserRequestTagRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'uuid', 'name', 'avatar', 'role']


class ReviewArtistTagRequestSerializer(serializers.ModelSerializer):
    artwork = ArtworkReviewDataSerializer()
    status = serializers.IntegerField()
    request_by = UserRequestTagRequestSerializer()
    request_to = UserSerializer()

    class Meta:
        model = ArtistTagRequest
        fields = (
            'id', 'artwork', 'created_at', 'updated_at', 'status',
            'request_by', 'request_to', 'message')


class RejectArtistTagRequestSerializer(serializers.Serializer):
    message = serializers.CharField(required=False, allow_blank=True)

    def process(self, certificate_request):
        certificate_request.status = STATUS_REQUEST.REQUEST_DENIED
        certificate_request.message = self.validated_data['message']
        certificate_request.save()


class ApproveArtistTagRequestSerializer(serializers.Serializer):
    artwork_link_id = serializers.IntegerField(required=False, allow_null=True)
    edition_link_number = serializers.IntegerField()
    requested_artwork_id = serializers.IntegerField()
    requested_edition_id = serializers.IntegerField()

    def validate_artwork_link_id(self, artwork_id):
        if not artwork_id:
            return None

        artwork = get_object_or_404(ArtWork, pk=artwork_id)
        return artwork

    def validate_requested_artwork_id(self, artwork_id):
        return get_object_or_404(ArtWork, pk=artwork_id)

    def validate_requested_edition_id(self, edition_id):
        return get_object_or_404(ArtworkEdition, pk=edition_id)

    def get_edition(self, artwork):
        edition = get_object_or_404(ArtworkEdition,
                                    edition_number=self.validated_data['edition_link_number'],
                                    artwork=artwork)
        return edition

    def process(self):
        user = self.context['request'].user
        artwork_link = self.validated_data.get('artwork_link_id', None)
        requested_edition = self.validated_data.get('requested_edition_id', None)
        requested_artwork = self.validated_data.get('requested_artwork_id', None)

        attribute_data = {
            'status': 'sold',
            'is_public': False,
            'owner': user,
        }

        if not artwork_link:
            artwork_link = copy_artwork(sample_artwork=requested_artwork, attribute_data=attribute_data)
            generate_artwork_edition(total_edition=requested_artwork.total_edition, artwork=artwork_link)

        requested_artwork.linked_artwork = artwork_link
        requested_artwork.save()

        edition_link = self.get_edition(artwork=artwork_link)
        requested_edition.linked_edition = edition_link
        requested_edition.save()

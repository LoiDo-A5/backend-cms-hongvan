from rest_framework import serializers
from django.core.paginator import Paginator, EmptyPage

from artwork.models import Collection, ArtWork, ImageArtwork
from artwork.serializers.artwork import SizeArtworkSerializer, MediumSerializer
from artwork.serializers.artwork import ArtworkArtistSerializer

from core.accounts.api.user_api import UserSerializer


class CollectionArtworkSerializer(serializers.ModelSerializer):
    images = serializers.ListField(read_only=True, child=serializers.ImageField())
    size = SizeArtworkSerializer()
    medium = MediumSerializer()
    artist_artwork = ArtworkArtistSerializer()

    class Meta:
        model = ArtWork
        fields = ('id', 'uuid', 'images', 'title', 'size', 'medium', 'is_public', 'artist_artwork')

    def to_representation(self, instance):
        images = ImageArtwork.objects.filter(artwork=instance)
        instance.images = [item.image for item in images]

        return super().to_representation(instance)


class CollectionWriteSerializer(serializers.ModelSerializer):
    artworks = serializers.PrimaryKeyRelatedField(queryset=ArtWork.objects.all(), many=True, required=False)

    class Meta:
        model = Collection
        fields = ('id', 'title', 'description', 'owner', 'artworks', 'is_public')


class BaseCollectionSerializer(serializers.ModelSerializer):
    artworks = serializers.SerializerMethodField()
    owner = UserSerializer()
    is_owner = serializers.BooleanField(read_only=True)
    artwork_ids = serializers.ListField()
    image = serializers.ImageField(read_only=True)
    number_of_likes = serializers.IntegerField(read_only=True)
    is_user_like = serializers.BooleanField(read_only=True)

    class Meta:
        model = Collection
        fields = ('id', 'uuid', 'title', 'description', 'owner', 'artworks', 'is_public', 'is_owner', 'artwork_ids',
                  'created_at', 'image', 'number_of_likes', 'is_user_like')

    def filter_artworks(self, instance, user):
        if instance.has_owner(user):
            return instance.artworks.all()
        return instance.artworks.filter(is_public=True)

    def to_representation(self, instance):
        user = self.context['request'].user
        instance.is_owner = instance.has_owner(user)

        artworks = self.filter_artworks(instance, user)
        instance.artwork_ids = [artwork.id for artwork in artworks]

        first_artwork = artworks.first()
        if first_artwork:
            artwork_image = first_artwork.imageartwork_set.first()
            instance.image = getattr(artwork_image, 'image', None)

        if not user.is_anonymous:
            instance.is_user_like = instance.like_collections.filter(user=user).exists()
        else:
            instance.is_user_like = False

        instance.number_of_likes = instance.like_collections.count()

        return super().to_representation(instance)


class CollectionReadSerializer(BaseCollectionSerializer):
    def get_artworks(self, instance):
        request = self.context.get('request')
        user = request.user if request else None
        artworks = self.filter_artworks(instance, user)

        # Pagination logic
        artworks_page = request.query_params.get('artworks_page', 1)
        artworks_page_size = request.query_params.get('artworks_page_size', 24)

        artworks_page = int(artworks_page)
        artworks_page_size = int(artworks_page_size)
        paginator = Paginator(artworks, artworks_page_size)

        try:
            paginated_artworks = paginator.page(artworks_page)
        except EmptyPage:
            paginated_artworks = []

        serialized_artworks = CollectionArtworkSerializer(paginated_artworks, many=True, context=self.context).data
        return {
            'page_size': artworks_page_size,
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'next': artworks_page + 1 if artworks_page < paginator.num_pages else None,
            'previous': artworks_page - 1 if artworks_page > 1 else None,
            'results': serialized_artworks,
        }


class CollectionReadForEditSerializer(BaseCollectionSerializer):
    def get_artworks(self, instance):
        user = self.context['request'].user
        artworks = self.filter_artworks(instance, user)
        return CollectionArtworkSerializer(artworks, many=True, context=self.context).data

from rest_framework import serializers

from artwork.models import ArtWork, SizeArtwork


class ArtworkCopySerializer(serializers.ModelSerializer):
    class Meta:
        model = ArtWork
        fields = (
            'artist_id',
            'title',
            'category',
            'orientation_id',
            'price',
            'currency',
            'year_created',
            'period_created',
            'total_edition',
            'piece',
            'artist_name',
            'description',
        )


class SizeArtworkCopySerializer(serializers.ModelSerializer):
    class Meta:
        model = SizeArtwork
        exclude = ('id',)

from rest_framework import serializers

from artwork.models import ColorArtwork


class ColorArtworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColorArtwork
        fields = (
            'id',
            'name',
            'category',
        )

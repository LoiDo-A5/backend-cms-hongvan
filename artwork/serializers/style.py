from rest_framework import serializers

from artwork.models import StyleArtwork


class StyleArtworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = StyleArtwork
        fields = (
            'id',
            'name',
            'name_vi',
            'category',
        )

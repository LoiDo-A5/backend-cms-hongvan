from rest_framework import serializers

from artwork.models import OrientationArtwork


class OrientationArtworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrientationArtwork
        fields = (
            'id',
            'name',
            'name_vi',
            'category',
        )

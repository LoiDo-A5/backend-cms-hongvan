from rest_framework import serializers

from artwork.models import SubjectArtwork


class SubjectArtworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubjectArtwork
        fields = (
            'id',
            'name',
            'name_vi',
            'category',
        )

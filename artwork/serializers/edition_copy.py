from rest_framework import serializers

from artwork.models import ArtworkEdition


class EditionCopySerializer(serializers.ModelSerializer):
    class Meta:
        model = ArtworkEdition
        fields = (
            'edition_number',
            'status',
        )

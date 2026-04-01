from rest_framework import serializers

from activity_log.models import CertificateLog
from artwork.models import ImageArtwork


class CertificateExportLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificateLog
        fields = '__all__'


class CertificateVerifyLogSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(read_only=True)
    title_artwork = serializers.CharField()

    class Meta:
        model = CertificateLog
        fields = ('created_at', 'image', 'title_artwork')

    def to_representation(self, instance):
        artwork = instance.certificate.artwork_edition.artwork
        images = ImageArtwork.objects.filter(artwork=artwork)
        instance.image = images.first().image if images.exists() else None
        instance.title_artwork = artwork.title

        return super().to_representation(instance)

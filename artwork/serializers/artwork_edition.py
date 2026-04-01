from rest_framework import serializers

from artwork.models import ArtworkEdition
from artwork.models import ArtworkCertificate
from artwork.models import ImageArtwork
from artwork.models import ArtWork
from artwork.models.artwork import CURRENCY_CHOICES
from artwork.serializers.artwork import OwnerCertificateSerializer
from artwork.serializers.artwork import CertificateSerializer
from artwork.serializers.artwork import LinkedEditionSerializer
from core.accounts.api.user_api import UserSerializer


class EditionSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    currency = serializers.ChoiceField(choices=CURRENCY_CHOICES, required=False, allow_null=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False, allow_null=True)

    id_certificate = serializers.SlugRelatedField(
        slug_field='code',
        read_only=True,
        source='certificate_alias',
        default=None,
    )
    owner_certificate = OwnerCertificateSerializer(source='certificate_alias.owner', read_only=True, default=None)
    linked_edition = LinkedEditionSerializer(allow_null=True)
    transferee = UserSerializer(read_only=True, allow_null=True)

    class Meta:
        model = ArtworkEdition
        fields = (
            'id',
            'edition_number',
            'owner_name',
            'currency',
            'price',
            'id_certificate',
            'owner_certificate',
            'status',
            'location',
            'linked_edition',
            'transferee',
        )

    def get_certificate(self, instance):
        certificate = getattr(instance, 'certificate', None)
        if certificate:
            return certificate

        linked_edition = getattr(instance, 'linked_edition_related', None)
        return getattr(linked_edition, 'certificate', None)

    def to_representation(self, instance):
        instance.certificate_alias = self.get_certificate(instance)
        return super().to_representation(instance)


class ArtworkEditionSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(read_only=True)
    editions = EditionSerializer(many=True, source='list_editions')
    certificate = CertificateSerializer(allow_null=True)

    class Meta:
        model = ArtWork
        fields = ('id', 'title', 'total_edition', 'image', 'editions', 'certificate')
        ref_name = 'ArtworkEditionSerializer'

    def to_representation(self, instance):
        certificate_available = (ArtworkCertificate.objects.filter(artwork_edition__artwork=instance,
                                                                   artwork_edition__status='available')
                                 .order_by('id').first())

        certificate_consignment = (ArtworkCertificate.objects.filter(artwork_edition__artwork=instance,
                                                                     artwork_edition__status='consignment')
                                   .order_by('id').first())
        instance.certificate = certificate_available if certificate_available else certificate_consignment
        image_obj = ImageArtwork.objects.filter(artwork=instance).first()
        instance.image = image_obj.image if image_obj else None
        instance.list_editions = instance.editions.all().order_by('edition_number')

        return super().to_representation(instance)

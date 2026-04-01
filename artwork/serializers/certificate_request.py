from django.conf import settings
from django.db.models import Q
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from rest_framework.generics import get_object_or_404
from django.utils.translation import gettext as _

from activity_log.models import CertificateLog
from activity_log.models import ArtworkLog
from activity_log.models.artwork_log import (
    ACTION_CERTIFICATE_ISSUED,
    ACTION_CERTIFICATE_REJECT,
)
from artwork.task.notification import notify_approve_certificate_request
from artwork.utils.artwork import copy_artwork, generate_artwork_edition
from artwork.models import CertificateRequest, ImageCertificateRequest, ArtWork, ArtworkEdition
from artwork.serializers.artwork_certificate import ArtworkShortSerializer
from artwork.models.artwork_certificate import ArtworkCertificate
from artwork.models.owner_certificate import OwnerCertificate
from artwork.models.certificate_request import STATUS
from artwork.serializers.artwork import ArtworkEditionSerializer
from core.accounts.api.user_api import UserSerializer
from core.accounts.models import User


class UserRequestRequestCerSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = (
            'name',
            'year_of_birth',
            'place_of_birth',
        )


class BaseCertificateRequestSerializer(serializers.ModelSerializer):
    artwork = ArtworkShortSerializer(source='artwork_edition.artwork')
    edition = ArtworkEditionSerializer(source='artwork_edition')
    status = serializers.IntegerField()
    request_by = UserRequestRequestCerSerializer()
    request_to = UserSerializer()

    class Meta:
        model = CertificateRequest
        fields = (
            'id', 'edition', 'owner_info', 'shipping_info', 'created_at', 'updated_at', 'artwork', 'status',
            'request_by', 'request_to', 'message')


class ReviewCertificateSerializer(BaseCertificateRequestSerializer):
    images = serializers.ListField(read_only=True, child=serializers.ImageField())
    key_images = serializers.ListField(read_only=True, child=serializers.CharField())
    signature = serializers.ImageField(source='artwork_edition.certificate.signature', read_only=True)
    view_url = serializers.URLField(allow_null=True)

    class Meta(BaseCertificateRequestSerializer.Meta):
        fields = BaseCertificateRequestSerializer.Meta.fields + ('images', 'key_images', 'signature', 'view_url')

    def to_representation(self, instance):
        images = ImageCertificateRequest.objects.filter(certificate_request=instance)
        instance.images = [item.image for item in images]
        instance.key_images = [item.image for item in images]

        edition = instance.artwork_edition
        certificate = getattr(edition, 'certificate', None)
        if certificate:
            instance.view_url = f'{settings.PRIMARY_SITE_URL}/view-certificate/{certificate.code}'

        return super().to_representation(instance)


class ApproveCertificateRequestSerializer(serializers.Serializer):
    artwork_link_id = serializers.IntegerField(required=False, allow_null=True)
    edition_link_number = serializers.IntegerField()

    def validate_artwork_link_id(self, artwork_id):
        if not artwork_id:
            return None

        artwork = get_object_or_404(ArtWork, pk=artwork_id)
        return artwork

    def get_edition(self, artwork):
        edition = get_object_or_404(ArtworkEdition,
                                    edition_number=self.validated_data['edition_link_number'],
                                    artwork=artwork)

        if edition.has_certificate():
            raise serializers.ValidationError('This edition already has certificate')
        return edition

    def create_certificate_logs(self, user, certificate):
        CertificateLog.objects.create(
            user=user,
            certificate=certificate,
            data=_(f"A certificate for the artwork '{certificate.artwork_edition.artwork.title}' was issued."),
        )

    def update_edition_and_artwork_status(self, edition, user=None):
        edition.status = 'available'
        edition.save()

        artwork = edition.artwork
        artwork.status = 'available'
        if user:
            artwork._current_user = user
        artwork.save()

    def process(self, certificate_request):
        user = self.context['request'].user
        artwork_link = self.validated_data.get('artwork_link_id', None)
        requested_edition = certificate_request.artwork_edition
        requested_artwork = requested_edition.artwork

        attribute_data = {
            'status': 'sold',
            'owner': user,
        }

        if not artwork_link:
            artwork_link = copy_artwork(sample_artwork=requested_artwork, attribute_data=attribute_data)
            generate_artwork_edition(total_edition=requested_artwork.total_edition, artwork=artwork_link)

        requested_artwork.artist_artwork = None
        requested_artwork.linked_artwork = artwork_link
        requested_artwork._current_user = user
        requested_artwork.save()

        artwork_link.status = 'sold'
        artwork_link.save()

        edition_link = self.get_edition(artwork=artwork_link)
        edition_link.status = 'sold'
        edition_link.save()
        requested_edition.linked_edition = edition_link
        requested_edition.save()

        certificate = ArtworkCertificate.objects.create(artwork_edition=certificate_request.artwork_edition,
                                                        issued_by=certificate_request.request_to,
                                                        issued_to=certificate_request.request_by)
        OwnerCertificate.objects.create(certificate=certificate, **certificate_request.owner_info)

        certificate_request.status = STATUS.REQUEST_APPROVED
        certificate_request.save()

        self.update_edition_and_artwork_status(requested_edition, user=user)

        # Create certificates for remaining eligible editions in artwork_link
        remaining_editions = (
            ArtworkEdition.objects.filter(artwork=artwork_link)
            .filter(certificate__isnull=True)
            .filter(Q(linked_edition__isnull=True) | Q(linked_edition__certificate__isnull=True))
            .filter(Q(linked_edition_related__isnull=True) | Q(linked_edition_related__certificate__isnull=True))
        )
        for remaining_edition in remaining_editions.iterator():
            remaining_certificate = ArtworkCertificate.objects.create(
                artwork_edition=remaining_edition,
                issued_by=user,
                issued_to=user,
            )
            OwnerCertificate.objects.create(
                certificate=remaining_certificate,
                user=user,
                name=getattr(user, 'legal_name', None) or getattr(user, 'name', None) or '',
            )
            self.update_edition_and_artwork_status(remaining_edition, user=user)

        params1 = {
            'field': 'certificate_request',
            'title': requested_artwork.title,
            'issued_to': certificate_request.request_by.name,
        }
        template_en1 = 'Issued certificate for artwork {title} (to: {issued_to})'
        template_vi1 = 'Đã cấp chứng nhận cho tác phẩm {title} (cho: {issued_to})'
        ArtworkLog.objects.create(
            artwork=requested_artwork,
            user=certificate_request.request_to,
            action_type=ACTION_CERTIFICATE_ISSUED,
            content_en=template_en1.format(**params1),
            content_vi=template_vi1.format(**params1),
            template_en=template_en1,
            template_vi=template_vi1,
            params=params1,
        )
        params2 = {
            'field': 'certificate_request',
            'title': requested_artwork.title,
            'issued_by': certificate_request.request_to.name,
        }
        template_en2 = 'Certificate issued for artwork {title} (by: {issued_by}).'
        template_vi2 = 'Chứng nhận đã được cấp cho tác phẩm {title} (bởi: {issued_by}).'
        ArtworkLog.objects.create(
            artwork=requested_artwork,
            user=certificate_request.request_by,
            action_type=ACTION_CERTIFICATE_ISSUED,
            content_en=template_en2.format(**params2),
            content_vi=template_vi2.format(**params2),
            template_en=template_en2,
            template_vi=template_vi2,
            params=params2,
        )
        self.create_certificate_logs(user, certificate)

        # Send notification to request_by user
        notify_approve_certificate_request.delay(
            request_user_id=certificate_request.request_by.id,
            issued_by_user_id=certificate_request.request_to.id,
            artwork_id=requested_artwork.id,
            certificate_id=certificate.id,
        )


class RejectCertificateRequestSerializer(serializers.Serializer):
    message = serializers.CharField(required=False, allow_blank=True)

    def process(self, certificate_request):
        certificate_request.status = STATUS.REQUEST_DENIED
        certificate_request.message = self.validated_data.get('message', '')
        certificate_request.save()
        requested_artwork = certificate_request.artwork_edition.artwork

        params_rej1 = {
            'field': 'certificate_request',
            'title': requested_artwork.title,
            'request_by': certificate_request.request_by.name,
        }
        template_en_rej1 = 'Rejected certificate request for artwork {title} (from: {request_by}).'
        template_vi_rej1 = 'Đã từ chối yêu cầu chứng nhận cho tác phẩm {title} (từ: {request_by}).'
        ArtworkLog.objects.create(
            artwork=requested_artwork,
            user=certificate_request.request_to,
            action_type=ACTION_CERTIFICATE_REJECT,
            content_en=template_en_rej1.format(**params_rej1),
            content_vi=template_vi_rej1.format(**params_rej1),
            template_en=template_en_rej1,
            template_vi=template_vi_rej1,
            params=params_rej1,
        )

        params_rej2 = {
            'field': 'certificate_request',
            'title': requested_artwork.title,
            'request_to': certificate_request.request_to.name,
        }
        template_en_rej2 = 'Your certificate request for artwork {title} was rejected (by: {request_to}).'
        template_vi_rej2 = 'Yêu cầu chứng nhận của bạn cho tác phẩm {title} đã bị từ chối (bởi: {request_to}).'
        ArtworkLog.objects.create(
            artwork=requested_artwork,
            user=certificate_request.request_by,
            action_type=ACTION_CERTIFICATE_REJECT,
            content_en=template_en_rej2.format(**params_rej2),
            content_vi=template_vi_rej2.format(**params_rej2),
            template_en=template_en_rej2,
            template_vi=template_vi_rej2,
            params=params_rej2,
        )


class UpdateCertificateRequestSerializer(serializers.ModelSerializer):
    images = serializers.ListField(write_only=True, child=serializers.CharField(), required=False)

    class Meta:
        model = CertificateRequest
        fields = ['id', 'status', 'owner_info', 'shipping_info', 'request_to', 'message', 'images']

    def validate(self, attrs):
        instance = self.instance
        user = self.context['request'].user

        if not user == instance.request_by:
            raise PermissionDenied({'detail': 'Permission denied.'})

        return super().validate(attrs)

    def update_images(self, instance, images):
        existing_images = ImageCertificateRequest.objects.filter(certificate_request=instance)
        existing_filenames = [image.image for image in existing_images]

        if not images:
            existing_images.delete()
        else:
            new_images = [
                ImageCertificateRequest(certificate_request=instance, image=image)
                for image in images if image not in existing_filenames
            ]
            ImageCertificateRequest.objects.bulk_create(new_images)

            (ImageCertificateRequest.objects.filter(certificate_request=instance, image__in=existing_filenames)
             .exclude(image__in=images).delete())

    def update(self, instance, validated_data):
        images = validated_data.pop('images', None)

        validated_data['status'] = STATUS.REQUEST_RECEIVED
        validated_data['message'] = ''
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        self.update_images(instance, images)
        instance.save()

        return instance

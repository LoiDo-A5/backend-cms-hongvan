from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from artwork.models import ArtworkCertificate
from artwork.models import ArtworkEdition
from artwork.models import ImageArtwork
from artwork.models.artwork import ArtWork
from artwork.serializers.artwork import ArtistSerializer
from artwork.serializers.artwork import GetOwnerCertificateSerializer
from artwork.serializers.artwork import StyleSerializer
from artwork.serializers.artwork import SubjectSerializer
from artwork.serializers.artwork import SizeArtworkSerializer
from artwork.serializers.artwork import MediumSerializer
from artwork.serializers.artwork_edition import EditionSerializer
from artwork.serializers.artwork import ArtworkArtistSerializer
from artwork.utils.const import CATEGORY_CHOICES
from common.serializers.common import ChoiceFieldSerializer
from core.accounts.api.user_api import UserSerializer
from core.accounts.models.user import User, USER_ROLE
from artwork.utils.artwork import copy_artwork, copy_artwork_edition
from activity_log.models import ArtworkLog
from activity_log.models.artwork_log import ACTION_UPDATE_ARTWORK
from core.accounts.tasks.notification import make_notification_message
from core.accounts.models.notification_template import NOTIFICATIONS_CONTENT_CODE


class LinkedArtworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArtWork
        fields = ('id', 'title')


class ArtworkShortSerializer(serializers.ModelSerializer):
    category = ChoiceFieldSerializer(choices=CATEGORY_CHOICES)
    size = SizeArtworkSerializer()
    medium = MediumSerializer()
    image = serializers.ImageField(read_only=True)
    style = StyleSerializer(required=False, allow_null=True)
    subject = SubjectSerializer(required=False, allow_null=True)
    images = serializers.ListField(read_only=True, child=serializers.ImageField())
    editions = EditionSerializer(read_only=True, many=True, source='list_editions')
    linked_artwork = LinkedArtworkSerializer()
    artist_artwork = ArtworkArtistSerializer()
    artist = ArtistSerializer()
    is_owner = serializers.BooleanField(read_only=True)
    has_certificate = serializers.BooleanField(read_only=True)

    class Meta:
        model = ArtWork
        fields = (
            'id',
            'active',
            'title',
            'owner',
            'title',
            'total_edition',
            'year_created',
            'period_created',
            'size',
            'medium',
            'image',
            'category',
            'price',
            'currency',
            'total_edition',
            'style',
            'subject',
            'orientation',
            'description',
            'images',
            'status',
            'total_edition',
            'editions',
            'linked_artwork',
            'artist_artwork',
            'artist',
            'is_owner',
            'has_certificate',
        )

    def to_representation(self, instance):
        images = ImageArtwork.objects.filter(artwork=instance)
        instance.image = images.first().image if images.exists() else None
        instance.images = [item.image for item in images]
        instance.list_editions = instance.editions.all().order_by('edition_number')
        user = self.context['request'].user
        instance.is_owner = instance.has_owner(user)
        instance.has_certificate = type(instance).has_certificate(instance)

        return super().to_representation(instance)


class ArtworkCertificateSerializer(serializers.ModelSerializer):
    artwork = ArtworkShortSerializer(source='artwork_edition.artwork')
    owner_certificate = GetOwnerCertificateSerializer(source='owner', read_only=True)
    edition_number = serializers.IntegerField(source='artwork_edition.edition_number')
    status = serializers.CharField(source='get_status_display')
    issued_by = UserSerializer()
    issued_to = UserSerializer()
    view_url = serializers.URLField()
    is_artist_owner_certificate = serializers.SerializerMethodField()

    class Meta:
        model = ArtworkCertificate
        fields = ('id', 'code', 'edition_number', 'created_at', 'updated_at', 'owner_certificate', 'artwork',
                  'signature', 'status', 'issued_by', 'issued_to', 'view_url', 'is_artist_owner_certificate')

    def to_representation(self, instance):
        instance.view_url = f'{settings.PRIMARY_SITE_URL}/view-certificate/{instance.code}'
        return super().to_representation(instance)

    def get_is_artist_owner_certificate(self, obj):
        request = self.context.get('request')
        return all([
            obj.issued_by_id is not None,
            obj.issued_to_id is not None,
            obj.issued_by_id == obj.issued_to_id,
            request.user.role == USER_ROLE.ARTIST,
        ])


class TransferOwnerSerializer(serializers.Serializer):
    recipient_user_id = serializers.IntegerField()

    def validate(self, attrs):
        request = self.context['request']
        certificate = self.context['certificate']
        current_user = request.user
        recipient_user_id = attrs.get('recipient_user_id')

        if current_user.role == USER_ROLE.ARTIST:
            raise PermissionDenied(
                detail={
                    'message': 'Artist role is not allowed to transfer ownership',
                },
            )

        if current_user.id != certificate.issued_to_id:
            raise PermissionDenied(
                detail={
                    'message': 'You are not the current owner of this certificate',
                },
            )

        recipient = get_object_or_404(User, id=recipient_user_id)

        if recipient.id == current_user.id:
            raise serializers.ValidationError(
                {
                    'message': 'Recipient must be different from current owner',
                },
                code='self_transfer',
            )

        attrs['recipient'] = recipient
        attrs['current_user'] = current_user
        return attrs

    def process(self):
        certificate = self.context['certificate']
        recipient = self.validated_data['recipient']
        current_user = self.validated_data['current_user']
        request = self.context['request']

        artwork = certificate.artwork_edition.artwork

        if artwork.owner_id == current_user.id:
            artwork_to_transfer = artwork
        else:
            artwork_to_transfer = artwork.linked_artworks.filter(
                owner_id=current_user.id,
            ).first()

        snapshot_data = None
        if current_user.role == USER_ROLE.COLLECTOR and artwork_to_transfer:
            from artwork.utils.collector_transfer_snapshot import build_collector_transfer_snapshot

            snapshot_data = build_collector_transfer_snapshot(artwork_to_transfer, request)

        with transaction.atomic():
            from_user_id = current_user.id
            to_user_id = recipient.id

            artwork_to_transfer.owner = recipient
            artwork_to_transfer.status = 'in_stock'
            artwork_to_transfer.in_stock_date = timezone.now().date()
            artwork_to_transfer.save(update_fields=['owner', 'status', 'in_stock_date', 'updated_at'])

            ArtworkEdition.objects.filter(artwork=artwork_to_transfer).update(status='in_stock')

            certificate.issued_to = recipient
            certificate.save(update_fields=['issued_to', 'updated_at'])

            owner_certificate = certificate.owner
            owner_certificate.user = recipient
            owner_certificate.name = recipient.legal_name
            owner_certificate.save(update_fields=['user', 'name'])

            if current_user.role == USER_ROLE.COLLECTOR and artwork_to_transfer and snapshot_data:
                from artwork.models import CollectorOwnershipTransfer

                CollectorOwnershipTransfer.objects.create(
                    transferrer=current_user,
                    transferee=recipient,
                    artwork=artwork_to_transfer,
                    certificate=certificate,
                    snapshot=snapshot_data,
                )

        inventory_code = getattr(artwork_to_transfer, 'inventory_code', None) or 'N/A'
        title = getattr(artwork_to_transfer, 'title', None) or f"Artwork #{getattr(artwork_to_transfer, 'pk', '?')}"

        params_sender = {
            'title': title,
            'inventory_code': inventory_code,
            'from_user': getattr(current_user, 'name', ''),
            'to_user': getattr(recipient, 'name', ''),
        }
        template_en_sender = (
            "Transferred ownership of artwork '{title}' (inventory code: {inventory_code}) "
            'from {from_user} to {to_user}'
        )
        template_vi_sender = (
            "Đã chuyển quyền sở hữu tác phẩm '{title}' (mã kiểm kê: {inventory_code}) "
            'từ {from_user} cho {to_user}'
        )
        ArtworkLog.objects.create(
            artwork=artwork_to_transfer,
            user=current_user,
            action_type=ACTION_UPDATE_ARTWORK,
            content_en=template_en_sender.format(**params_sender),
            content_vi=template_vi_sender.format(**params_sender),
            template_en=template_en_sender,
            template_vi=template_vi_sender,
            params=params_sender,
        )

        params_recipient = {
            'title': title,
            'inventory_code': inventory_code,
            'from_user': getattr(current_user, 'name', ''),
        }
        template_en_recipient = (
            "Received ownership of artwork '{title}' (inventory code: {inventory_code}) "
            'from {from_user}'
        )
        template_vi_recipient = (
            "Đã nhận quyền sở hữu tác phẩm '{title}' (mã kiểm kê: {inventory_code}) "
            'từ {from_user}'
        )
        ArtworkLog.objects.create(
            artwork=artwork_to_transfer,
            user=recipient,
            action_type=ACTION_UPDATE_ARTWORK,
            content_en=template_en_recipient.format(**params_recipient),
            content_vi=template_vi_recipient.format(**params_recipient),
            template_en=template_en_recipient,
            template_vi=template_vi_recipient,
            params=params_recipient,
        )

        make_notification_message(
            user=recipient,
            content_code=NOTIFICATIONS_CONTENT_CODE.TRANSFER_OWNERSHIP_RECIPIENT,
            content_params={
                'artwork_title': title,
                'artwork_uuid': str(artwork_to_transfer.uuid),
                'from_user_name': getattr(current_user, 'name', ''),
            },
            notification_kwargs={
                'icon': getattr(current_user, 'avatar', None),
            },
            push_kwargs={
                'data': {
                    'content_code': NOTIFICATIONS_CONTENT_CODE.TRANSFER_OWNERSHIP_RECIPIENT,
                    'params': {
                        'artwork_uuid': str(artwork_to_transfer.uuid),
                    },
                },
            },
            credentials=None,
        )

        return {
            'certificate': certificate,
            'from_user_id': from_user_id,
            'to_user_id': to_user_id,
        }


class TransferOwnerWithRoleArtistSerializer(serializers.Serializer):
    recipient_user_id = serializers.IntegerField()

    def validate(self, attrs):
        request = self.context['request']
        certificate = self.context['certificate']
        current_user = request.user
        recipient_user_id = attrs.get('recipient_user_id')

        if not all([
            certificate.issued_by_id is not None,
            certificate.issued_to_id is not None,
            certificate.issued_by_id == certificate.issued_to_id,
            current_user.role == USER_ROLE.ARTIST,
        ]):
            raise serializers.ValidationError({
                'message': 'You do not have permission to transfer this certificate',
            })

        recipient = get_object_or_404(User, id=recipient_user_id)

        attrs['recipient'] = recipient
        attrs['current_user'] = current_user
        return attrs

    def process(self):
        certificate = self.context['certificate']
        recipient = self.validated_data['recipient']
        current_user = self.validated_data['current_user']

        with transaction.atomic():
            edition = certificate.artwork_edition

            sample_artwork = edition.artwork
            attribute_data = {
                'owner': recipient,
            }
            artwork_copy = copy_artwork(sample_artwork=sample_artwork, attribute_data=attribute_data)

            edition_attribute_data = {
                'artwork_id': artwork_copy.id,
            }
            edition_copy = copy_artwork_edition(sample_edition=edition, attribute_data=edition_attribute_data)

            artwork_copy.linked_artwork = edition.artwork
            artwork_copy.status = 'in_stock'
            artwork_copy.in_stock_date = timezone.now().date()
            artwork_copy.save()

            edition_copy.artwork = artwork_copy
            edition_copy.linked_edition = edition
            edition_copy.status = 'in_stock'
            edition_copy.save()

            original_artwork = edition.artwork
            original_artwork.status = 'sold'
            edition.status = 'sold'
            edition.transferee = recipient
            original_artwork.save()
            edition.save()

            certificate.issued_to = recipient
            certificate.save(update_fields=['issued_to', 'updated_at'])

            owner_certificate = certificate.owner
            owner_certificate.user = recipient
            owner_certificate.name = recipient.legal_name
            owner_certificate.save(update_fields=['user', 'name'])

            original_artwork.disable_certificate_sync()

        base_artwork = edition.artwork
        inventory_code = getattr(base_artwork, 'inventory_code', None) or 'N/A'
        title = getattr(base_artwork, 'title', None) or f"Artwork #{getattr(base_artwork, 'pk', '?')}"

        params_sender = {
            'title': title,
            'inventory_code': inventory_code,
            'from_user': getattr(current_user, 'name', ''),
            'to_user': getattr(recipient, 'name', ''),
        }
        template_en_sender = (
            "Transferred ownership of artwork '{title}' (inventory code: {inventory_code}) "
            'from {from_user} to {to_user}'
        )
        template_vi_sender = (
            "Đã chuyển quyền sở hữu tác phẩm '{title}' (mã kiểm kê: {inventory_code}) "
            'từ {from_user} cho {to_user}'
        )
        ArtworkLog.objects.create(
            artwork=base_artwork,
            user=current_user,
            action_type=ACTION_UPDATE_ARTWORK,
            content_en=template_en_sender.format(**params_sender),
            content_vi=template_vi_sender.format(**params_sender),
            template_en=template_en_sender,
            template_vi=template_vi_sender,
            params=params_sender,
        )

        params_recipient = {
            'title': title,
            'inventory_code': inventory_code,
            'from_user': getattr(current_user, 'name', ''),
        }
        template_en_recipient = (
            "Received ownership of artwork '{title}' (inventory code: {inventory_code}) "
            'from {from_user}'
        )
        template_vi_recipient = (
            "Đã nhận quyền sở hữu tác phẩm '{title}' (mã kiểm kê: {inventory_code}) "
            'từ {from_user}'
        )
        ArtworkLog.objects.create(
            artwork=base_artwork,
            user=recipient,
            action_type=ACTION_UPDATE_ARTWORK,
            content_en=template_en_recipient.format(**params_recipient),
            content_vi=template_vi_recipient.format(**params_recipient),
            template_en=template_en_recipient,
            template_vi=template_vi_recipient,
            params=params_recipient,
        )

        make_notification_message(
            user=recipient,
            content_code=NOTIFICATIONS_CONTENT_CODE.TRANSFER_OWNERSHIP_RECIPIENT,
            content_params={
                'artwork_title': title,
                'artwork_id': artwork_copy.id,
                'artwork_uuid': str(artwork_copy.uuid),
                'from_user_name': getattr(current_user, 'name', ''),
            },
            notification_kwargs={
                'icon': getattr(current_user, 'avatar', None),
            },
            push_kwargs={
                'data': {
                    'content_code': NOTIFICATIONS_CONTENT_CODE.TRANSFER_OWNERSHIP_RECIPIENT,
                    'params': {
                        'artwork_uuid': str(artwork_copy.uuid),
                    },
                },
            },
            credentials=None,
        )

        return {
            'certificate': certificate,
            'from_user_id': recipient.id,
            'to_user_id': current_user.id,
        }


class TransferOwnerArtworkWithRoleArtistSerializer(serializers.Serializer):
    edition_id = serializers.IntegerField()
    recipient_user_id = serializers.IntegerField()

    def validate(self, attrs):
        request = self.context['request']
        current_user = request.user
        edition_id = attrs.get('edition_id')
        recipient_user_id = attrs.get('recipient_user_id')

        if current_user.role != USER_ROLE.ARTIST:
            raise serializers.ValidationError({
                'message': 'You do not have permission to transfer this artwork',
            })

        edition = get_object_or_404(ArtworkEdition, id=edition_id)

        if edition.has_certificate():
            raise serializers.ValidationError({
                'message': 'Edition already has a certificate and cannot be transferred',
            })

        if ArtworkEdition.objects.filter(linked_edition=edition).exists():
            raise serializers.ValidationError({
                'message': 'This edition has already been linked to a transferred edition',
            })

        artwork = edition.artwork

        if artwork.owner_id != current_user.id:
            raise PermissionDenied({'message': 'You are not the owner of this artwork'})

        recipient = get_object_or_404(User, id=recipient_user_id)

        attrs['recipient'] = recipient
        attrs['current_user'] = current_user
        attrs['artwork'] = artwork
        attrs['edition'] = edition
        return attrs

    def process(self):
        recipient = self.validated_data['recipient']
        current_user = self.validated_data['current_user']
        base_artwork = self.validated_data['artwork']
        base_edition = self.validated_data['edition']

        with transaction.atomic():
            attribute_data = {
                'owner': recipient,
            }
            artwork_copy = copy_artwork(sample_artwork=base_artwork, attribute_data=attribute_data)

            edition_attribute_data = {
                'artwork_id': artwork_copy.id,
            }
            edition_copy = copy_artwork_edition(sample_edition=base_edition, attribute_data=edition_attribute_data)

            artwork_copy.linked_artwork = base_artwork
            artwork_copy.status = 'in_stock'
            artwork_copy.save()

            edition_copy.artwork = artwork_copy
            edition_copy.linked_edition = base_edition
            edition_copy.status = 'in_stock'
            edition_copy.save()

            base_edition.transferee = recipient
            base_edition.save(update_fields=['transferee'])

            base_artwork.disable_certificate_sync()

        inventory_code = getattr(base_artwork, 'inventory_code', None) or 'N/A'
        title = getattr(base_artwork, 'title', None) or f"Artwork #{getattr(base_artwork, 'pk', '?')}"

        params_sender = {
            'title': title,
            'inventory_code': inventory_code,
            'from_user': getattr(current_user, 'name', ''),
            'to_user': getattr(recipient, 'name', ''),
        }
        template_en_sender = (
            "Transferred ownership of artwork '{title}' (inventory code: {inventory_code}) "
            'from {from_user} to {to_user}'
        )
        template_vi_sender = (
            "Đã chuyển quyền sở hữu tác phẩm '{title}' (mã kiểm kê: {inventory_code}) "
            'từ {from_user} cho {to_user}'
        )
        ArtworkLog.objects.create(
            artwork=base_artwork,
            user=current_user,
            action_type=ACTION_UPDATE_ARTWORK,
            content_en=template_en_sender.format(**params_sender),
            content_vi=template_vi_sender.format(**params_sender),
            template_en=template_en_sender,
            template_vi=template_vi_sender,
            params=params_sender,
        )

        params_recipient = {
            'title': title,
            'inventory_code': inventory_code,
            'from_user': getattr(current_user, 'name', ''),
        }
        template_en_recipient = (
            "Received ownership of artwork '{title}' (inventory code: {inventory_code}) "
            'from {from_user}'
        )
        template_vi_recipient = (
            "Đã nhận quyền sở hữu tác phẩm '{title}' (mã kiểm kê: {inventory_code}) "
            'từ {from_user}'
        )
        ArtworkLog.objects.create(
            artwork=base_artwork,
            user=recipient,
            action_type=ACTION_UPDATE_ARTWORK,
            content_en=template_en_recipient.format(**params_recipient),
            content_vi=template_vi_recipient.format(**params_recipient),
            template_en=template_en_recipient,
            template_vi=template_vi_recipient,
            params=params_recipient,
        )

        make_notification_message(
            user=recipient,
            content_code=NOTIFICATIONS_CONTENT_CODE.TRANSFER_OWNERSHIP_RECIPIENT,
            content_params={
                'artwork_title': title,
                'artwork_id': artwork_copy.id,
                'artwork_uuid': str(artwork_copy.uuid),
                'from_user_name': getattr(current_user, 'name', ''),
            },
            notification_kwargs={
                'icon': getattr(current_user, 'avatar', None),
            },
            push_kwargs={
                'data': {
                    'content_code': NOTIFICATIONS_CONTENT_CODE.TRANSFER_OWNERSHIP_RECIPIENT,
                    'params': {
                        'artwork_uuid': str(artwork_copy.uuid),
                    },
                },
            },
            credentials=None,
        )

        return {
            'from_user_id': current_user.id,
            'to_user_id': recipient.id,
            'artwork_id': artwork_copy.id,
        }

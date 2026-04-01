from rest_framework import serializers
from django.utils import timezone

from artwork.models import Collection, ShareLink
from core.accounts.api.user_api import UserSerializer
from core.accounts.models import User
from core.accounts.models.notification_template import NOTIFICATIONS_CONTENT_CODE
from core.accounts.tasks.notification import make_notification_message


class ShareLinkCreateSerializer(serializers.ModelSerializer):
    has_expiration = serializers.BooleanField(write_only=True, required=False, default=False)
    has_password = serializers.BooleanField(write_only=True, required=False, default=False)
    is_share_all = serializers.BooleanField(required=False, default=False)
    collection_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        default=list,
    )
    recipient_user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
        default=list,
    )

    banner = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = ShareLink
        fields = [
            'title', 'description', 'artwork', 'recipient_type',
            'recipient_user_ids', 'collection_ids', 'expiration_type', 'share_type',
            'has_expiration', 'has_password', 'password', 'expires_at', 'banner', 'is_share_all',
        ]

    def validate_expiration_type(self, value):
        if value == 'custom':
            expires_at = self.initial_data.get('expires_at')
            if not expires_at:
                raise serializers.ValidationError(
                    'Expiration date must be provided when expiration_type is custom',
                )

        return value

    def validate_expires_at(self, value):
        if value and value <= timezone.now():
            raise serializers.ValidationError(
                'Expiration date must be in the future',
            )
        return value

    def validate(self, attrs):
        is_share_all = attrs.get('is_share_all', False)
        artwork = attrs.get('artwork')

        if not is_share_all:
            if not artwork:
                raise serializers.ValidationError({
                    'artwork': 'At least one artwork must be selected',
                })

        return attrs

    def process_send_notification(self, share_link, recipient_user_ids):
        request = self.context.get('request')
        users = User.objects.filter(id__in=recipient_user_ids)

        for user in users:
            share_link.add_recipient(user)

            content_code = NOTIFICATIONS_CONTENT_CODE.SHARE_LINK_INVITATION if share_link.title else (
                NOTIFICATIONS_CONTENT_CODE.SHARE_LINK_INVITATION_NO_TITLE)

            make_notification_message(
                user=user,
                content_code=content_code,
                content_params={
                    'from_user_name': getattr(request.user, 'name', '') or getattr(
                        request.user, 'username', '',
                    ),
                    'share_link_title': share_link.title or '',
                    'share_link_id': str(share_link.id),
                },
            )

    def create(self, validated_data):
        validated_data.pop('has_expiration', None)
        validated_data.pop('has_password', None)
        collection_ids = validated_data.pop('collection_ids', [])
        recipient_user_ids = validated_data.pop('recipient_user_ids', [])
        recipient_type = validated_data.get('recipient_type')

        artwork_ids = validated_data.pop('artwork', [])
        share_type = validated_data.get('share_type')

        share_link = super().create(validated_data)
        request = self.context.get('request')

        if share_link.share_type == 'collection':
            collections = Collection.objects.filter(owner=request.user, id__in=collection_ids)
            share_link.collections.set(collections)

        if share_type == 'artwork':
            share_link.artwork.set(artwork_ids)

        if recipient_type == 'specific':
            self.process_send_notification(share_link, recipient_user_ids)

        return share_link


class ShareLinkDetailSerializer(serializers.ModelSerializer):
    is_expired = serializers.ReadOnlyField()
    is_valid = serializers.ReadOnlyField()
    share_url = serializers.SerializerMethodField()
    banner = serializers.ImageField(required=False, allow_null=True)
    artwork_count = serializers.SerializerMethodField()
    recipients_count = serializers.SerializerMethodField()
    recipients_ids = serializers.SerializerMethodField()
    user = UserSerializer()

    class Meta:
        model = ShareLink
        fields = [
            'id', 'title', 'description', 'expires_at', 'is_expired',
            'is_valid', 'created_at', 'access_count', 'share_url',
            'share_type', 'recipient_type', 'expiration_type', 'artwork_count',
            'recipients_count', 'recipients_ids', 'banner', 'is_share_all', 'user',
        ]

    def get_share_url(self, obj):
        request = self.context.get('request')
        return obj.get_share_url(request)

    def get_artwork_count(self, obj):
        return obj.artwork.count()

    def get_recipients_count(self, obj):
        return obj.recipients.count()

    def get_recipients_ids(self, obj):
        return list(obj.recipients.values_list('id', flat=True))


class ShareLinkListSerializer(serializers.ModelSerializer):
    is_expired = serializers.ReadOnlyField()
    is_valid = serializers.ReadOnlyField()
    share_url = serializers.SerializerMethodField()
    artwork_count = serializers.SerializerMethodField()

    class Meta:
        model = ShareLink
        fields = [
            'id', 'title', 'description', 'expires_at', 'is_expired',
            'is_valid', 'created_at', 'access_count', 'share_url',
            'share_type', 'recipient_type', 'artwork_count', 'is_share_all',
        ]

    def get_share_url(self, obj):
        request = self.context.get('request')
        return obj.get_share_url(request)

    def get_artwork_count(self, obj):
        return obj.artwork.count()


class ShareLinkAccessSerializer(serializers.Serializer):
    password = serializers.CharField()


class ShareLinkItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()
    title = serializers.CharField()
    image = serializers.CharField(allow_null=True)
    owner = serializers.CharField()


class ShareLinkUpdateSerializer(serializers.ModelSerializer):
    banner = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = ShareLink
        fields = [
            'title',
            'description',
            'recipient_type',
            'expiration_type',
            'expires_at',
            'password',
            'banner',
        ]

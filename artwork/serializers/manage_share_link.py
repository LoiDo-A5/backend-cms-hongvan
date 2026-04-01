from rest_framework import serializers
from django.conf import settings
from django.utils import timezone

from artwork.models import ShareLink


class ManageShareLinkSerializer(serializers.ModelSerializer):
    is_expired = serializers.ReadOnlyField()
    is_valid = serializers.ReadOnlyField()
    share_url = serializers.SerializerMethodField()
    artwork_count = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    recipients_count = serializers.SerializerMethodField()

    class Meta:
        model = ShareLink
        fields = [
            'id', 'title', 'description', 'share_type', 'recipient_type',
            'expiration_type', 'expires_at', 'is_active', 'is_share_all',
            'created_at', 'updated_at', 'access_count',
            'is_expired', 'is_valid', 'share_url',
            'artwork_count', 'recipients_count', 'status',
        ]

    def get_share_url(self, obj):
        return f'{settings.PRIMARY_SITE_URL}/share/{obj.id}'

    def get_artwork_count(self, obj):
        if obj.is_share_all:
            from artwork.models import ArtWork
            return ArtWork.objects.filter(owner=obj.user).count()
        return obj.artwork.count()

    def get_recipients_count(self, obj):
        return obj.recipients.count()

    def get_status(self, obj):
        if not obj.is_active:
            return 'inactive'
        if obj.expiration_type != 'never' and obj.expires_at and obj.expires_at <= timezone.now():
            return 'expired'
        return 'active'


class ExtendShareLinkSerializer(serializers.Serializer):
    expiration_type = serializers.ChoiceField(choices=['custom', 'permanent', 'never'])
    expires_at = serializers.DateTimeField(required=False, allow_null=True)

    def validate(self, attrs):
        expiration_type = attrs.get('expiration_type')
        expires_at = attrs.get('expires_at')

        if expiration_type == 'custom':
            if not expires_at:
                raise serializers.ValidationError({
                    'expires_at': 'Expiration date is required when expiration_type is custom.',
                })
            if expires_at <= timezone.now():
                raise serializers.ValidationError({
                    'expires_at': 'Expiration date must be in the future.',
                })

        if expiration_type in ('permanent', 'never'):
            attrs['expires_at'] = None

        return attrs

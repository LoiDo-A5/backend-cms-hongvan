from rest_framework import serializers

from core.accounts.models.notification import Notification
from core.accounts.models.notification_template import NotificationTemplate


class NotificationTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationTemplate
        fields = ('id', 'content_code', 'title_en', 'title_vi', 'content_vi', 'content_en', 'redirect')


class NotificationSerializer(serializers.ModelSerializer):
    template = NotificationTemplateSerializer()
    title_vi = serializers.CharField(source='template.title_vi', allow_null=True)
    title_en = serializers.CharField(source='template.title_en', allow_null=True)

    class Meta:
        model = Notification
        fields = ('id', 'content_code', 'params', 'title_vi', 'title_en', 'content_en', 'content_vi',
                  'is_read', 'icon', 'redirect_url', 'template')


class NotificationNumber(serializers.Serializer):
    unread = serializers.IntegerField()
    unseen = serializers.IntegerField()

from rest_framework import serializers

from activity_log.models import ArtworkLog


class ArtworkLogSerializer(serializers.ModelSerializer):
    formatted_timestamp = serializers.SerializerMethodField()

    class Meta:
        model = ArtworkLog
        fields = (
            'id',
            'content_en',
            'content_vi',
            'template_en',
            'template_vi',
            'params',
            'action_type',
            'created_at',
            'formatted_timestamp',
        )
        read_only_fields = ('id', 'created_at')

    def get_formatted_timestamp(self, obj):
        if obj.created_at:
            return obj.created_at.strftime('%d %b %Y %H:%M:%S')
        return None

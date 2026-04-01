from rest_framework import serializers

from core.photobooth.models import CapturePackage


class CapturePackageSerializer(serializers.ModelSerializer):
    """Payload cho FE booth (Electron / web)."""

    amount = serializers.IntegerField(source='amount_vnd', read_only=True)
    lines = serializers.SerializerMethodField()

    class Meta:
        model = CapturePackage
        fields = (
            'id',
            'code',
            'name',
            'amount',
            'print_count',
            'include_online_file',
            'lines',
            'sort_order',
            'is_active',
        )
        read_only_fields = fields

    def get_lines(self, obj):
        lines = [obj.description_line_1]
        if obj.description_line_2:
            lines.append(obj.description_line_2)
        return lines

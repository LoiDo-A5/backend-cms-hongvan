from rest_framework import serializers

from core.photobooth.models import CapturePackage


class CapturePackageSerializer(serializers.ModelSerializer):
    """Payload cho FE booth (Electron / web)."""

    amount = serializers.IntegerField(source='amount_vnd', read_only=True)
    lines = serializers.SerializerMethodField()
    lines_en = serializers.SerializerMethodField()

    class Meta:
        model = CapturePackage
        fields = (
            'id',
            'code',
            'name',
            'name_en',
            'amount',
            'print_count',
            'include_online_file',
            'lines',
            'lines_en',
            'sort_order',
            'is_active',
        )
        read_only_fields = fields

    def get_lines(self, obj):
        lines = [obj.description_line_1]
        if obj.description_line_2:
            lines.append(obj.description_line_2)
        return lines

    def get_lines_en(self, obj):
        lines = [obj.description_line_1_en] if obj.description_line_1_en else []
        if obj.description_line_2_en:
            lines.append(obj.description_line_2_en)
        return lines


class CapturePackageWriteSerializer(serializers.ModelSerializer):
    """CMS write serializer — tạo/sửa gói chụp."""

    class Meta:
        model = CapturePackage
        fields = (
            'id',
            'code',
            'name',
            'name_en',
            'amount_vnd',
            'print_count',
            'include_online_file',
            'description_line_1',
            'description_line_1_en',
            'description_line_2',
            'description_line_2_en',
            'sort_order',
            'is_active',
        )
        read_only_fields = ('id',)

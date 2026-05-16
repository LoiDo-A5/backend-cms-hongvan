import json
import re
from uuid import uuid4

from django.core.files.storage import default_storage
from rest_framework import serializers

from core.projects.models import Project


class ProjectListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = (
            'id',
            'name',
            'is_visible',
            'active',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'active', 'created_at', 'updated_at')


class ProjectPublicCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = (
            'id',
            'website_card_title',
            'website_card_content',
            'website_card_thumbnail',
        )
        read_only_fields = fields


class ProjectPublicDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = (
            'id',
            'name',
            'website_card_title',
            'website_card_content',
            'website_card_thumbnail',
            'hero_title',
            'hero_content',
            'hero_image',
            'section_background_mode',
            'section_background_color',
            'section_background_image',
            'features',
            'cta_title',
            'cta_content',
            'cta_button_label',
            'cta_button_url',
            'project_video',
            'long_description_title',
            'long_description',
            'accordion_background_image',
            'accordion_items',
        )
        read_only_fields = fields


class ProjectSerializer(serializers.ModelSerializer):
    website_card_thumbnail = serializers.ImageField(required=False, allow_null=True)
    hero_image = serializers.ImageField(required=False, allow_null=True)
    section_background_image = serializers.ImageField(required=False, allow_null=True)
    accordion_background_image = serializers.ImageField(required=False, allow_null=True)
    project_video = serializers.FileField(required=False, allow_null=True)
    clear_website_card_thumbnail = serializers.BooleanField(required=False, write_only=True, default=False)
    clear_hero_image = serializers.BooleanField(required=False, write_only=True, default=False)
    clear_section_background_image = serializers.BooleanField(required=False, write_only=True, default=False)
    clear_accordion_background_image = serializers.BooleanField(required=False, write_only=True, default=False)
    clear_project_video = serializers.BooleanField(required=False, write_only=True, default=False)
    features = serializers.JSONField(required=False)
    accordion_items = serializers.JSONField(required=False)

    class Meta:
        model = Project
        fields = (
            'id',
            'name',
            'is_visible',
            'active',
            'website_card_title',
            'website_card_content',
            'website_card_thumbnail',
            'clear_website_card_thumbnail',
            'hero_title',
            'hero_content',
            'hero_image',
            'clear_hero_image',
            'section_background_mode',
            'section_background_color',
            'section_background_image',
            'clear_section_background_image',
            'features',
            'cta_title',
            'cta_content',
            'cta_button_label',
            'cta_button_url',
            'project_video',
            'clear_project_video',
            'long_description_title',
            'long_description',
            'accordion_title',
            'accordion_background_image',
            'clear_accordion_background_image',
            'accordion_items',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'active', 'created_at', 'updated_at')
        extra_kwargs = {
            'name': {'required': False, 'allow_blank': True},
            'website_card_title': {'required': False, 'allow_blank': True},
            'website_card_content': {'required': False, 'allow_blank': True},
            'hero_title': {'required': False, 'allow_blank': True},
            'hero_content': {'required': False, 'allow_blank': True},
            'section_background_color': {'required': False, 'allow_blank': True, 'allow_null': True},
            'cta_title': {'required': False, 'allow_blank': True},
            'cta_content': {'required': False, 'allow_blank': True},
            'cta_button_label': {'required': False, 'allow_blank': True},
            'cta_button_url': {'required': False, 'allow_blank': True},
            'long_description_title': {'required': False, 'allow_blank': True},
            'long_description': {'required': False, 'allow_blank': True},
            'accordion_title': {'required': False, 'allow_blank': True},
        }

    def to_internal_value(self, data):
        if hasattr(data, 'items'):
            data = {key: data.get(key) for key in data.keys()}

        for field_name in ('features', 'accordion_items'):
            raw_value = data.get(field_name)
            if isinstance(raw_value, str) and raw_value:
                try:
                    data[field_name] = json.loads(raw_value)
                except json.JSONDecodeError as exc:
                    raise serializers.ValidationError({field_name: 'Dữ liệu JSON không hợp lệ.'}) from exc

        return super().to_internal_value(data)

    def validate_features(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('Danh sách tính năng phải là một mảng.')
        return value

    def validate_accordion_items(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError('Danh sách accordion phải là một mảng.')
        return value

    def validate_section_background_color(self, value):
        normalized = (value or '').strip()
        if not normalized:
            return None

        if not re.fullmatch(r'#[0-9A-Fa-f]{6}', normalized):
            raise serializers.ValidationError('Màu nền section phải có định dạng HEX, ví dụ #030303.')

        return normalized.upper()

    def validate(self, attrs):
        attrs = super().validate(attrs)
        primary_name = (
            attrs.get('website_card_title')
            or attrs.get('hero_title')
            or attrs.get('name')
            or getattr(self.instance, 'name', '')
        )

        if not primary_name:
            raise serializers.ValidationError({
                'website_card_title': 'Vui lòng nhập tiêu đề thẻ hiển thị ngoài website.',
            })

        attrs['name'] = primary_name
        section_background_mode = attrs.get(
            'section_background_mode',
            getattr(self.instance, 'section_background_mode', Project.SECTION_BACKGROUND_MODE_COLOR),
        )
        attrs['section_background_mode'] = section_background_mode

        if section_background_mode == Project.SECTION_BACKGROUND_MODE_COLOR:
            if 'section_background_color' not in attrs and self.instance is not None:
                attrs['section_background_color'] = self.instance.section_background_color

        elif self.instance is None and 'section_background_color' not in attrs:
            attrs['section_background_color'] = None

        return attrs

    def create(self, validated_data):
        # Remove clear_* fields that are only for updates
        validated_data.pop('clear_website_card_thumbnail', False)
        validated_data.pop('clear_hero_image', False)
        validated_data.pop('clear_section_background_image', False)
        validated_data.pop('clear_accordion_background_image', False)
        validated_data.pop('clear_project_video', False)
        
        features = validated_data.pop('features', [])
        project = super().create(validated_data)
        project.features = self._attach_feature_icons(features)
        project.save(update_fields=['features'])
        return project

    def update(self, instance, validated_data):
        clear_file_fields = {
            'website_card_thumbnail': validated_data.pop('clear_website_card_thumbnail', False),
            'hero_image': validated_data.pop('clear_hero_image', False),
            'section_background_image': validated_data.pop('clear_section_background_image', False),
            'accordion_background_image': validated_data.pop('clear_accordion_background_image', False),
            'project_video': validated_data.pop('clear_project_video', False),
        }
        features = validated_data.pop('features', None)
        project = super().update(instance, validated_data)

        cleared_fields = []
        for field_name, should_clear in clear_file_fields.items():
            if not should_clear:
                continue

            field_file = getattr(project, field_name)
            if field_file:
                field_file.delete(save=False)
            setattr(project, field_name, None)
            cleared_fields.append(field_name)

        if cleared_fields:
            project.save(update_fields=cleared_fields)

        if features is not None:
            project.features = self._attach_feature_icons(features, existing=project.features)
            project.save(update_fields=['features'])
        return project

    def _attach_feature_icons(self, features, existing=None):
        request = self.context.get('request')
        uploaded_files = getattr(request, 'FILES', None)
        existing = existing or []
        normalized_features = []

        for index, feature in enumerate(features):
            normalized_feature = dict(feature)
            upload_key = f'feature_icon_{index}'
            uploaded_file = uploaded_files.get(upload_key) if uploaded_files else None

            if uploaded_file is not None:
                file_name = default_storage.save(
                    f'projects/features/{uuid4()}_{uploaded_file.name}',
                    uploaded_file,
                )
                normalized_feature['icon_url'] = default_storage.url(file_name)
            elif index < len(existing) and isinstance(existing[index], dict):
                existing_icon_url = existing[index].get('icon_url')
                if existing_icon_url and 'icon_url' not in normalized_feature:
                    normalized_feature['icon_url'] = existing_icon_url

            normalized_features.append(normalized_feature)

        return normalized_features


class ProjectListResponseSerializer(serializers.Serializer):
    counts = serializers.DictField(child=serializers.IntegerField())
    results = ProjectListSerializer(many=True)
from rest_framework import serializers

from core.photobooth.models import (
    PhotoboothBackground,
    PhotoboothDecorFrame,
    PhotoboothFilter,
    PhotoboothSticker,
)


class PhotoboothFilterOptionSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = PhotoboothFilter
        fields = ('id', 'code', 'name', 'sort_order', 'image_url')

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        url = obj.image.url
        if request:
            return request.build_absolute_uri(url)
        return url


class PhotoboothDecorFrameOptionSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = PhotoboothDecorFrame
        fields = ('id', 'code', 'name', 'sort_order', 'image_url')

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        url = obj.image.url
        if request:
            return request.build_absolute_uri(url)
        return url


class PhotoboothBackgroundOptionSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = PhotoboothBackground
        fields = ('id', 'code', 'name', 'sort_order', 'image_url')

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        url = obj.image.url
        if request:
            return request.build_absolute_uri(url)
        return url


class PhotoboothStickerOptionSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = PhotoboothSticker
        fields = ('id', 'code', 'name', 'sort_order', 'image_url')

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get('request')
        url = obj.image.url
        if request:
            return request.build_absolute_uri(url)
        return url

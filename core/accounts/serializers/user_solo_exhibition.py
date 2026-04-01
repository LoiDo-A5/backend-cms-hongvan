from rest_framework import serializers

from core.accounts.models import UserSoloExhibition


class SoloExhibitionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSoloExhibition
        fields = ('year', 'description', 'is_public', 'exhibition_link', 'to_year')

    def create(self, validated_data):
        user = self.context['request'].user
        exhibition = UserSoloExhibition.objects.create(user=user, **validated_data)
        return exhibition


class SoloExhibitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSoloExhibition
        fields = '__all__'

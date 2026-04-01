from rest_framework import serializers

from core.accounts.models import UserPublication


class PublicationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPublication
        fields = ('year', 'description', 'is_public')

    def create(self, validated_data):
        user = self.context['request'].user
        exhibition = UserPublication.objects.create(user=user, **validated_data)
        return exhibition


class PublicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPublication
        fields = '__all__'

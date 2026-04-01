from rest_framework import serializers

from core.accounts.models import UserGroupExhibition


class GroupExhibitionCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserGroupExhibition
        fields = ('year', 'description', 'is_public', 'exhibition_link', 'to_year')

    def create(self, validated_data):
        user = self.context['request'].user
        exhibition = UserGroupExhibition.objects.create(user=user, **validated_data)
        return exhibition


class GroupExhibitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserGroupExhibition
        fields = '__all__'

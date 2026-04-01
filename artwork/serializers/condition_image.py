from rest_framework import serializers

from artwork.models.condition_image_batch import ConditionImage
from core.accounts.api.user_api import UserSerializer


class ConditionImageSerializer(serializers.ModelSerializer):
    owner = UserSerializer(source='batch.owner', read_only=True)
    created_at = serializers.DateTimeField(source='batch.created_at', read_only=True)

    class Meta:
        model = ConditionImage
        fields = ('id', 'owner', 'created_at', 'image')

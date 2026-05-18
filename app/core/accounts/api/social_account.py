from allauth.socialaccount.models import SocialAccount
from dj_rest_auth.registration.views import SocialAccountListView
from rest_framework import serializers


class SocialAccountSerializer(serializers.ModelSerializer):
    extra_data = serializers.JSONField()

    class Meta:
        model = SocialAccount
        fields = (
            'id',
            'provider',
            'uid',
            'extra_data',
        )


class SocialAccountApi(SocialAccountListView):
    serializer_class = SocialAccountSerializer

from rest_framework import serializers
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated

from core.accounts.models import User


class ReferralFriendsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.CharField()


class ReferralFriendsApi(ListAPIView):
    queryset = User.objects.all()
    serializer_class = ReferralFriendsSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return self.request.user.referrals.all().order_by('-date_joined')

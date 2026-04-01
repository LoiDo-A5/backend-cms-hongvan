from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from core.accounts.models import UserVisibleSetting
from core.accounts.api.user_profile import UserVisibleSettingSerializer


class UserVisibleSettingApi(GenericAPIView):
    serializer_class = UserVisibleSettingSerializer
    permission_classes = (IsAuthenticated,)

    def patch(self, request):
        instance, created = UserVisibleSetting.objects.get_or_create(user=request.user)

        serializer = self.get_serializer(instance=instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

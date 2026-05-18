from django.conf import settings
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class FeaturesApi(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        start_with = 'accounts.feature_'
        permissions = request.user.get_all_permissions()
        feature_permissions = [x for x in permissions if x.startswith(start_with)]
        start_index = len(start_with)
        active_features = {x[start_index:] for x in feature_permissions}

        return Response(active_features.union(settings.ENABLED_FEATURES))

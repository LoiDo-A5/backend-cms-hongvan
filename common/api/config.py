from django.core.cache import cache
from packaging import version
from rest_framework import serializers
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response


class ConfigSerializer(serializers.Serializer):
    version = serializers.CharField()

    def validate(self, attrs):
        version_text = attrs['version']
        platform = self.context['platform']
        lowest_version = cache.get(f'FORCE_UPGRADE_VERSION_{platform}')

        if not lowest_version:
            need_upgrade = False
        else:
            need_upgrade = version.parse(version_text) < version.parse(lowest_version)

        return {
            'upgrade': need_upgrade,
        }


class ConfigApi(GenericAPIView):
    platform = ''

    serializer_class = ConfigSerializer

    def get_serializer_context(self):
        context = super(ConfigApi, self).get_serializer_context()
        context['platform'] = self.platform
        return context

    def get(self, request):
        serializer = self.get_serializer(data=request.GET)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.validated_data)

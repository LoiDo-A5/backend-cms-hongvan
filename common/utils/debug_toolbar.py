from django.conf import settings


def show_toolbar(request):  # pragma: nocover
    return request.META.get('HTTP_DEBUG', None) == settings.DEBUG_HEADER

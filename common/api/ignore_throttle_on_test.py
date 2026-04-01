from django.conf import settings


class IgnoreThrottleOnTestMixin:
    def get_throttles(self):
        if settings.IS_TEST:
            return []
        return super().get_throttles()

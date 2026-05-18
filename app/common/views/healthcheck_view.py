from django.core.cache import cache
from django.http import HttpResponse
from django.views import View

from core.accounts.models import User


class HealthCheckView(View):
    def get(self, request):
        if not request.GET.get('skip_db'):
            User.objects.exists()  # check database connection
        cache.get('test-key')  # check redis cache
        return HttpResponse('OK')

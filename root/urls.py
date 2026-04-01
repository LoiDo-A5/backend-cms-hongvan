from django.conf import settings
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import include
from django.urls import path
from django.views.generic import TemplateView
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView
from two_factor.urls import urlpatterns as tf_urls

from common.views.healthcheck_view import HealthCheckView
from core.accounts.views.login_view import LoginView
from django.conf.urls.static import static

urlpatterns = [
    path('healthcheck/', HealthCheckView.as_view(), name='healthcheck'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page=settings.LOGOUT_REDIRECT_URL), name='logout'),

    path('api/', include(tf_urls)),

    path('api/common/', include('common.api_urls')),
    path('api/accounts/', include('core.accounts.api_urls')),
    path('api/accounts/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/accounts/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('policy/', TemplateView.as_view(template_name='policy.html')),
    path('toc/', TemplateView.as_view(template_name='toc.html')),
    path('', TemplateView.as_view(template_name='index.html')),
    path('accounts/', include('allauth.urls'), name='socialaccount_signup'),
    path('admin/', admin.site.urls),
]

schema_view = get_schema_view(
    openapi.Info(
        title='PhotoBook API',
        default_version='v1',
        description='PhotoBook backend API',
        terms_of_service='https://www.google.com/policies/terms/',
        contact=openapi.Contact(email='support@example.com'),
        license=openapi.License(name='MIT License'),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns += [
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static('/media/', document_root=settings.MEDIA_ROOT)

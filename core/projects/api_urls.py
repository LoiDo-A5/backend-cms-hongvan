from django.urls import include
from django.urls import path
from rest_framework import routers

from core.projects.api.project_api import ProjectViewSet

router = routers.SimpleRouter()
router.register(r'projects', ProjectViewSet, basename='projects')

urlpatterns = [
    path('', include(router.urls)),
]
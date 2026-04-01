from django.urls import path

from core.photobooth.api.capture_package_list_view import CapturePackageListView

urlpatterns = [
    path('packages/', CapturePackageListView.as_view(), name='photobooth-packages-list'),
]

from django.urls import path

from core.photobooth.api.capture_options_view import CaptureOptionsView
from core.photobooth.api.capture_package_list_view import CapturePackageListView
from core.photobooth.api.device_register_view import PhotoboothDeviceRegisterView

urlpatterns = [
    path('packages/', CapturePackageListView.as_view(), name='photobooth-packages-list'),
    path('devices/register/', PhotoboothDeviceRegisterView.as_view(), name='photobooth-device-register'),
    path('capture-options/', CaptureOptionsView.as_view(), name='photobooth-capture-options'),
]

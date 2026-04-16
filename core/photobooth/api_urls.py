from django.urls import path

from core.photobooth.api.capture_options_view import CaptureOptionsView
from core.photobooth.api.capture_package_crud_view import CapturePackageCrudView, CapturePackageDetailCrudView
from core.photobooth.api.capture_package_list_view import CapturePackageListView
from core.photobooth.api.device_register_view import PhotoboothDeviceRegisterView
from core.photobooth.api.order_gallery_view import OrderGalleryView
from core.photobooth.api.printer_error_view import PrinterErrorView
from core.photobooth.api.printer_status_view import PrinterStatusListView, PrinterStatusUpdateView
from core.photobooth.api.remove_background_view import RemoveBackgroundView
from core.photobooth.api.save_images_view import SaveImagesView

urlpatterns = [
    path('packages/', CapturePackageListView.as_view(), name='photobooth-packages-list'),
    # CMS CRUD (admin-only)
    path('cms/packages/', CapturePackageCrudView.as_view(), name='photobooth-cms-packages'),
    path('cms/packages/<int:pk>/', CapturePackageDetailCrudView.as_view(), name='photobooth-cms-package-detail'),
    path('devices/register/', PhotoboothDeviceRegisterView.as_view(), name='photobooth-device-register'),
    path('devices/printer-status/', PrinterStatusUpdateView.as_view(), name='photobooth-printer-status-update'),
    path('devices/printer-status/list/', PrinterStatusListView.as_view(), name='photobooth-printer-status-list'),
    path('printer-error/', PrinterErrorView.as_view(), name='photobooth-printer-error'),
    path('capture-options/', CaptureOptionsView.as_view(), name='photobooth-capture-options'),
    path('remove-background/', RemoveBackgroundView.as_view(), name='photobooth-remove-background'),
    path('save-images/', SaveImagesView.as_view(), name='photobooth-save-images'),
    path('gallery/<str:order_id>/', OrderGalleryView.as_view(), name='photobooth-order-gallery'),
]

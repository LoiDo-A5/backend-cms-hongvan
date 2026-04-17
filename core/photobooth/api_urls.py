from django.urls import path

from core.photobooth.api.background_crud_view import BackgroundCrudView, BackgroundDetailCrudView
from core.photobooth.api.capture_options_view import CaptureOptionsView
from core.photobooth.api.capture_package_crud_view import CapturePackageCrudView, CapturePackageDetailCrudView
from core.photobooth.api.cms_photos_view import CmsPhotosView
from core.photobooth.api.dashboard_view import DashboardView
from core.photobooth.api.capture_package_list_view import CapturePackageListView
from core.photobooth.api.decor_frame_crud_view import DecorFrameCrudView, DecorFrameDetailCrudView
from core.photobooth.api.device_register_view import PhotoboothDeviceRegisterView
from core.photobooth.api.order_gallery_view import OrderGalleryView
from core.photobooth.api.order_list_view import OrderListView
from core.photobooth.api.printer_error_view import PrinterErrorView
from core.photobooth.api.printer_status_view import PrinterStatusListView, PrinterStatusUpdateView
from core.photobooth.api.remove_background_view import RemoveBackgroundView
from core.photobooth.api.revenue_view import RevenueView
from core.photobooth.api.save_images_view import SaveImagesView
from core.photobooth.api.sticker_crud_view import StickerCrudView, StickerDetailCrudView

urlpatterns = [
    path('packages/', CapturePackageListView.as_view(), name='photobooth-packages-list'),
    # CMS CRUD (admin-only)
    path('cms/packages/', CapturePackageCrudView.as_view(), name='photobooth-cms-packages'),
    path('cms/packages/<int:pk>/', CapturePackageDetailCrudView.as_view(), name='photobooth-cms-package-detail'),
    path('cms/revenue/', RevenueView.as_view(), name='photobooth-cms-revenue'),
    path('cms/dashboard/', DashboardView.as_view(), name='photobooth-cms-dashboard'),
    path('cms/stickers/', StickerCrudView.as_view(), name='photobooth-cms-stickers'),
    path('cms/stickers/<int:pk>/', StickerDetailCrudView.as_view(), name='photobooth-cms-sticker-detail'),
    path('cms/backgrounds/', BackgroundCrudView.as_view(), name='photobooth-cms-backgrounds'),
    path('cms/backgrounds/<int:pk>/', BackgroundDetailCrudView.as_view(), name='photobooth-cms-background-detail'),
    path('cms/decor-frames/', DecorFrameCrudView.as_view(), name='photobooth-cms-decor-frames'),
    path('cms/decor-frames/<int:pk>/', DecorFrameDetailCrudView.as_view(), name='photobooth-cms-decor-frame-detail'),
    path('cms/orders/', OrderListView.as_view(), name='photobooth-cms-orders'),
    path('cms/photos/', CmsPhotosView.as_view(), name='photobooth-cms-photos'),
    path('devices/register/', PhotoboothDeviceRegisterView.as_view(), name='photobooth-device-register'),
    path('devices/printer-status/', PrinterStatusUpdateView.as_view(), name='photobooth-printer-status-update'),
    path('devices/printer-status/list/', PrinterStatusListView.as_view(), name='photobooth-printer-status-list'),
    path('printer-error/', PrinterErrorView.as_view(), name='photobooth-printer-error'),
    path('capture-options/', CaptureOptionsView.as_view(), name='photobooth-capture-options'),
    path('remove-background/', RemoveBackgroundView.as_view(), name='photobooth-remove-background'),
    path('save-images/', SaveImagesView.as_view(), name='photobooth-save-images'),
    path('gallery/<str:order_id>/', OrderGalleryView.as_view(), name='photobooth-order-gallery'),
]

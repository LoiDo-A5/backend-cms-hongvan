from django.urls import path

from core.photobooth.api.vietqr_create_views import VietqrCreatePaymentView
from core.photobooth.api.vietqr_views import VietqrWebhookView
from core.photobooth.api.vnpay_views import (
    PaymentStatusView,
    VnpayCreatePaymentView,
    VnpayIpnView,
    VnpayReturnView,
)

urlpatterns = [
    path('vietqr/create/', VietqrCreatePaymentView.as_view(), name='vietqr-create'),
    path('vnpay/create/', VnpayCreatePaymentView.as_view(), name='vnpay-create'),
    path('vnpay/ipn/', VnpayIpnView.as_view(), name='vnpay-ipn'),
    path('vnpay/return/', VnpayReturnView.as_view(), name='vnpay-return'),
    path('vietqr/webhook/', VietqrWebhookView.as_view(), name='vietqr-webhook'),
    path('status/<str:order_id>/', PaymentStatusView.as_view(), name='payment-status'),
]

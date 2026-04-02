from django.urls import path

from core.photobooth.api.vnpay_views import (
    PaymentStatusView,
    VnpayCreatePaymentView,
    VnpayIpnView,
    VnpayReturnView,
)

urlpatterns = [
    path('vnpay/create/', VnpayCreatePaymentView.as_view(), name='vnpay-create'),
    path('vnpay/ipn/', VnpayIpnView.as_view(), name='vnpay-ipn'),
    path('vnpay/return/', VnpayReturnView.as_view(), name='vnpay-return'),
    path('status/<str:order_id>/', PaymentStatusView.as_view(), name='payment-status'),
]

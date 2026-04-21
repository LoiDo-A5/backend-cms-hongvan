from django.urls import path

from core.payments.payos_views import (
    PayosCreatePaymentView,
    PayosWebhookView,
    PayosReturnView,
    PayosCancelReturnView,
)
from core.payments.paypal_views import (
    PaypalCreatePaymentView,
    PaypalReturnView,
    PaypalCancelView,
)
from core.payments.vnpay_views import (
    PaymentStatusView,
    VnpayCreatePaymentView,
    VnpayIpnView,
    VnpayReturnView,
)

urlpatterns = [
    path('payos/create/', PayosCreatePaymentView.as_view(), name='payos-create'),
    path('payos/webhook/', PayosWebhookView.as_view(), name='payos-webhook'),
    path('payos/return/', PayosReturnView.as_view(), name='payos-return'),
    path('payos/cancel/', PayosCancelReturnView.as_view(), name='payos-cancel'),
    path('vnpay/create/', VnpayCreatePaymentView.as_view(), name='vnpay-create'),
    path('vnpay/ipn/', VnpayIpnView.as_view(), name='vnpay-ipn'),
    path('vnpay/return/', VnpayReturnView.as_view(), name='vnpay-return'),
    path('paypal/create/', PaypalCreatePaymentView.as_view(), name='paypal-create'),
    path('paypal/return/', PaypalReturnView.as_view(), name='paypal-return'),
    path('paypal/cancel/', PaypalCancelView.as_view(), name='paypal-cancel'),
    path('status/<str:order_id>/', PaymentStatusView.as_view(), name='payment-status'),
]

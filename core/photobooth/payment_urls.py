from django.urls import path

from core.photobooth.api.payos_views import (
    PayosCreatePaymentView,
    PayosWebhookView,
    PayosReturnView,
    PayosCancelReturnView,
)
from core.photobooth.api.vnpay_views import PaymentStatusView

urlpatterns = [
    path('payos/create/', PayosCreatePaymentView.as_view(), name='payos-create'),
    path('payos/webhook/', PayosWebhookView.as_view(), name='payos-webhook'),
    path('payos/return/', PayosReturnView.as_view(), name='payos-return'),
    path('payos/cancel/', PayosCancelReturnView.as_view(), name='payos-cancel'),
    path('status/<str:order_id>/', PaymentStatusView.as_view(), name='payment-status'),
]

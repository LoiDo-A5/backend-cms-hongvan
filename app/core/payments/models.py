from django.db import models


class PaymentOrder(models.Model):
    """Đơn thanh toán: VNPAY, payOS (VietQR), PayPal."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Chờ thanh toán'
        PAID = 'paid', 'Đã thanh toán'
        FAILED = 'failed', 'Thất bại'
        EXPIRED = 'expired', 'Hết hạn'

    class PaymentMethod(models.TextChoices):
        VIETQR = 'vietqr', 'VietQR (payOS)'
        VNPAY = 'vnpay', 'VNPAY'
        PAYPAL = 'paypal', 'PayPal'

    txn_ref = models.CharField(max_length=100, unique=True, db_index=True)
    amount_vnd = models.PositiveIntegerField()
    description = models.CharField(max_length=255, blank=True, default='')

    # Generic metadata — điền tùy dự án (ví dụ: package_id, order_code, ...)
    extra_data = models.JSONField(default=dict, blank=True)

    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    payment_method = models.CharField(
        max_length=16,
        choices=PaymentMethod.choices,
        default=PaymentMethod.VIETQR,
        verbose_name='Phương thức thanh toán',
        db_index=True,
    )

    # payOS
    payos_order_code = models.BigIntegerField(null=True, blank=True, db_index=True)
    payos_payment_link_id = models.CharField(max_length=64, blank=True, default='')

    # PayPal
    paypal_order_id = models.CharField(max_length=64, blank=True, default='', db_index=True)

    # VNPAY
    vnp_transaction_no = models.CharField(max_length=32, blank=True, default='')
    vnp_response_code = models.CharField(max_length=8, blank=True, default='')
    vnp_transaction_status = models.CharField(max_length=8, blank=True, default='')

    expires_at = models.DateTimeField(db_index=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-id']
        verbose_name = 'Đơn thanh toán'
        verbose_name_plural = 'Đơn thanh toán'

    def __str__(self):
        return f'{self.txn_ref} ({self.status})'

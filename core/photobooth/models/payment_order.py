from django.db import models

from core.photobooth.models.capture_package import CapturePackage


class PaymentOrder(models.Model):
    """Đơn thanh toán: VNPAY (`txn_ref`), hoặc payOS (`payos_order_code`, `payos_payment_link_id`)."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Chờ thanh toán'
        PAID = 'paid', 'Đã thanh toán'
        FAILED = 'failed', 'Thất bại'
        EXPIRED = 'expired', 'Hết hạn'

    txn_ref = models.CharField(max_length=100, unique=True, db_index=True)
    amount_vnd = models.PositiveIntegerField()
    capture_package = models.ForeignKey(
        CapturePackage,
        on_delete=models.PROTECT,
        related_name='payment_orders',
        verbose_name='Gói chụp đi kèm đơn',
        help_text='Gói chụp mà khách đã chọn khi tạo đơn VNPAY này.',
    )
    device = models.ForeignKey(
        'photobooth.PhotoboothDevice',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payment_orders',
        verbose_name='Thiết bị photobooth',
        help_text='Thiết bị đã tạo đơn thanh toán này.',
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    booth_id = models.CharField(max_length=64, blank=True, default='')

    payos_order_code = models.BigIntegerField(null=True, blank=True, db_index=True)
    payos_payment_link_id = models.CharField(max_length=64, blank=True, default='')

    vnp_transaction_no = models.CharField(max_length=32, blank=True, default='')
    vnp_response_code = models.CharField(max_length=8, blank=True, default='')
    vnp_transaction_status = models.CharField(max_length=8, blank=True, default='')

    expires_at = models.DateTimeField(db_index=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'photobooth_payment_order'
        ordering = ['-id']
        verbose_name = 'Đơn thanh toán'
        verbose_name_plural = 'Đơn thanh toán'

    def __str__(self):
        return f'{self.txn_ref} ({self.status})'

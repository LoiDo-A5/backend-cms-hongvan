from django.db import models

from core.photobooth.models.payment_order import PaymentOrder


class ImagePhotobooth(models.Model):
    """Ảnh chụp từ booth, gắn với đơn thanh toán (PaymentOrder)."""

    payment_order = models.ForeignKey(
        PaymentOrder,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name='Đơn thanh toán',
    )
    image = models.ImageField(
        upload_to='photobooth/images/%Y/%m/%d/',
        verbose_name='Ảnh chụp',
    )
    round_index = models.PositiveSmallIntegerField(
        default=0,
        help_text='Thứ tự lượt chụp (0-based).',
    )
    photo_index = models.PositiveSmallIntegerField(
        default=0,
        help_text='Thứ tự ảnh trong lượt (0-based).',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'photobooth_image'
        ordering = ['payment_order', 'round_index', 'photo_index', 'id']
        verbose_name = 'Ảnh Photobooth'
        verbose_name_plural = 'Ảnh Photobooth'

    def __str__(self):
        return f'Image #{self.id} — Order {self.payment_order.txn_ref} (R{self.round_index}/P{self.photo_index})'

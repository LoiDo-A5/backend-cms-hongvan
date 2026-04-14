from django.db import models


class PhotoboothDecorFrame(models.Model):
    """
    Khung trang trí (overlay) sau chụp; một thiết bị có nhiều khung qua PhotoboothDevice.decor_frames.
    """

    LAYOUT_TYPE_CHOICES = [
        ('grid4', '4 lần chụp (lưới)'),
        ('strip4', '4 lần chụp (dọc)'),
        ('grid6', '6 lần chụp'),
    ]

    type = models.CharField(
        max_length=16,
        choices=LAYOUT_TYPE_CHOICES,
        blank=True,
        null=True,
        default=None,
        help_text='Loại layout: grid4, strip4, grid6. Để trống = hiển thị cho tất cả.',
    )
    code = models.SlugField(
        max_length=64,
        unique=True,
        help_text='Mã cố định cho API/FE, ví dụ: classic-gold, polaroid-01',
    )
    name = models.CharField(max_length=120)
    image = models.ImageField(
        upload_to='photobooth/decor_frames/',
        blank=True,
        null=True,
        help_text='Ảnh thumbnail / preview khung trên UI.',
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'photobooth_decor_frame'
        ordering = ['sort_order', 'id']
        verbose_name = 'Khung trang trí'
        verbose_name_plural = 'Khung trang trí'

    def __str__(self):
        return f'{self.name} ({self.code})'

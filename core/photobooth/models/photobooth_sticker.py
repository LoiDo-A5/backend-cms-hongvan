from django.db import models


class PhotoboothSticker(models.Model):
    """
    Sticker overlay cho photobooth; gán cho nhiều thiết bị qua PhotoboothDevice.stickers (M2M).
    """

    code = models.SlugField(
        max_length=64,
        unique=True,
        help_text='Mã cố định cho API/FE, ví dụ: stk-happy, stk-cat',
    )
    name = models.CharField(max_length=120, blank=True, default='')
    image = models.ImageField(
        upload_to='photobooth/stickers/',
        blank=True,
        null=True,
        help_text='Ảnh sticker (PNG trong suốt).',
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'photobooth_sticker'
        ordering = ['sort_order', 'id']
        verbose_name = 'Sticker'
        verbose_name_plural = 'Stickers'

    def __str__(self):
        return self.name or self.code

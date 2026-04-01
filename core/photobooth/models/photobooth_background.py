from django.db import models


class PhotoboothBackground(models.Model):
    """
    Background màn chụp; gán cho nhiều thiết bị qua PhotoboothDevice.backgrounds.
    """

    code = models.SlugField(
        max_length=64,
        unique=True,
        help_text='Mã cố định cho API/FE, ví dụ: bg-1, museum-wall',
    )
    name = models.CharField(max_length=120, blank=True, default='')
    image = models.ImageField(
        upload_to='photobooth/backgrounds/',
        blank=True,
        null=True,
        help_text='Ảnh nền / preview (tùy chọn).',
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'photobooth_background'
        ordering = ['sort_order', 'id']
        verbose_name = 'Background'
        verbose_name_plural = 'Backgrounds'

    def __str__(self):
        return self.name or self.code

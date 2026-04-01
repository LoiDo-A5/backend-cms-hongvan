from django.db import models


class PhotoboothFilter(models.Model):
    """
    Filter hiển thị trên màn chụp; gán cho nhiều thiết bị qua PhotoboothDevice.filters.
    """

    code = models.SlugField(
        max_length=64,
        unique=True,
        help_text='Mã cố định cho API/FE, ví dụ: hong-hao, vintage',
    )
    name = models.CharField(max_length=120)
    image = models.ImageField(
        upload_to='photobooth/filters/',
        blank=True,
        null=True,
        help_text='Ảnh thumbnail / preview filter (tùy chọn).',
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'photobooth_filter'
        ordering = ['sort_order', 'id']
        verbose_name = 'Filter'
        verbose_name_plural = 'Filters'

    def __str__(self):
        return f'{self.name} ({self.code})'

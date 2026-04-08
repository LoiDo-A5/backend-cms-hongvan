from django.db import models


class CapturePackage(models.Model):
    """
    Gói chụp / in hiển thị trên booth (có thể tạo/sửa trong Admin).
    `code` dùng làm khóa ổn định cho FE (economy, basic, premium, ...).
    """

    code = models.SlugField(
        max_length=64,
        unique=True,
        help_text='Mã cố định, ví dụ: economy, basic, premium',
    )
    name = models.CharField(max_length=120)
    name_en = models.CharField(max_length=120, blank=True, verbose_name='Name (EN)')
    amount_vnd = models.PositiveIntegerField(help_text='Số tiền VND (vd: 59000)')
    print_count = models.PositiveSmallIntegerField(
        default=1,
        help_text='Số ảnh in trong gói',
    )
    include_online_file = models.BooleanField(
        default=True,
        verbose_name='Nhận file online',
    )
    description_line_1 = models.CharField(max_length=255)
    description_line_1_en = models.CharField(max_length=255, blank=True, verbose_name='Description line 1 (EN)')
    description_line_2 = models.CharField(max_length=255, blank=True)
    description_line_2_en = models.CharField(max_length=255, blank=True, verbose_name='Description line 2 (EN)')
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'photobooth_capture_package'
        ordering = ['sort_order', 'id']
        verbose_name = 'Gói chụp'
        verbose_name_plural = 'Gói chụp'

    def __str__(self):
        return f'{self.name} ({self.code})'

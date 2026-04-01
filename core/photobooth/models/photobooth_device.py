from django.db import models


class PhotoboothDevice(models.Model):
    """
    Mỗi giá trị device_id (UUID lưu trên máy) tương ứng đúng một bản ghi: trường device_id
    có unique=True — không thể có hai dòng với cùng mã. App Electron chỉ tạo một UUID
    và ghi vào một file; mỗi lần đăng ký chỉ cập nhật cùng bản ghi (get_or_create).
    Chỉ khi xóa file / dữ liệu app máy mới sinh UUID mới → bản ghi thiết bị mới trên server.
    """

    device_id = models.CharField(
        max_length=128,
        unique=True,
        db_index=True,
        help_text='Duy nhất toàn hệ thống — một device_id = một máy (một bản ghi).',
    )
    name = models.CharField(
        max_length=200,
        help_text='Tên hiển thị; client có thể gửi khi đăng ký hoặc để server dùng tên mặc định.',
    )
    is_active = models.BooleanField(default=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'photobooth_device'
        verbose_name = 'Thiết bị photobooth'
        verbose_name_plural = 'Thiết bị photobooth'

    def __str__(self):
        return f'{self.name} ({self.device_id[:8]}…)'


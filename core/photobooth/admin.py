from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from core.photobooth.models import (
    CapturePackage,
    PaymentOrder,
    PhotoboothBackground,
    PhotoboothDecorFrame,
    PhotoboothDevice,
    PhotoboothFilter,
)


@admin.register(CapturePackage)
class CapturePackageAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'amount_vnd',
        'print_count',
        'sort_order',
        'is_active',
    )
    list_filter = ('is_active',)
    search_fields = ('code', 'name')
    ordering = ('sort_order', 'id')


@admin.register(PhotoboothFilter)
class PhotoboothFilterAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'image_thumb',
        'code',
        'name',
        'device_count',
        'sort_order',
        'is_active',
        'updated_at',
    )
    list_filter = ('is_active',)
    search_fields = ('code', 'name')
    ordering = ('sort_order', 'id')
    readonly_fields = ('created_at', 'updated_at', 'image_thumb_large')
    fieldsets = (
        (None, {'fields': ('code', 'name', 'is_active', 'sort_order')}),
        ('Ảnh preview', {'fields': ('image', 'image_thumb_large')}),
        ('Hệ thống', {'fields': ('created_at', 'updated_at')}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_device_count=Count('devices', distinct=True))

    @admin.display(description='Ảnh')
    def image_thumb(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="44" height="44" alt="" '
                'style="object-fit:cover;border-radius:4px;border:1px solid #ddd;" />',
                obj.image.url,
            )
        return '—'

    @admin.display(description='Xem trước')
    def image_thumb_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:240px;max-height:240px;object-fit:contain;border-radius:8px;border:1px solid #ddd;" />',
                obj.image.url,
            )
        return '—'

    @admin.display(description='Số thiết bị', ordering='_device_count')
    def device_count(self, obj):
        return obj._device_count


@admin.register(PhotoboothBackground)
class PhotoboothBackgroundAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'image_thumb',
        'code',
        'name',
        'device_count',
        'sort_order',
        'is_active',
        'updated_at',
    )
    list_filter = ('is_active',)
    search_fields = ('code', 'name')
    ordering = ('sort_order', 'id')
    readonly_fields = ('created_at', 'updated_at', 'image_thumb_large')
    fieldsets = (
        (None, {'fields': ('code', 'name', 'is_active', 'sort_order')}),
        ('Ảnh preview', {'fields': ('image', 'image_thumb_large')}),
        ('Hệ thống', {'fields': ('created_at', 'updated_at')}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_device_count=Count('devices', distinct=True))

    @admin.display(description='Ảnh')
    def image_thumb(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="44" height="44" alt="" '
                'style="object-fit:cover;border-radius:4px;border:1px solid #ddd;" />',
                obj.image.url,
            )
        return '—'

    @admin.display(description='Xem trước')
    def image_thumb_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:240px;max-height:240px;object-fit:contain;border-radius:8px;border:1px solid #ddd;" />',
                obj.image.url,
            )
        return '—'

    @admin.display(description='Số thiết bị', ordering='_device_count')
    def device_count(self, obj):
        return obj._device_count


@admin.register(PhotoboothDecorFrame)
class PhotoboothDecorFrameAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'image_thumb',
        'code',
        'name',
        'device_count',
        'sort_order',
        'is_active',
        'updated_at',
    )
    list_filter = ('is_active',)
    search_fields = ('code', 'name')
    ordering = ('sort_order', 'id')
    readonly_fields = ('created_at', 'updated_at', 'image_thumb_large')
    fieldsets = (
        (None, {'fields': ('code', 'name', 'is_active', 'sort_order')}),
        ('Ảnh preview', {'fields': ('image', 'image_thumb_large')}),
        ('Hệ thống', {'fields': ('created_at', 'updated_at')}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_device_count=Count('devices', distinct=True))

    @admin.display(description='Ảnh')
    def image_thumb(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" width="44" height="44" alt="" '
                'style="object-fit:cover;border-radius:4px;border:1px solid #ddd;" />',
                obj.image.url,
            )
        return '—'

    @admin.display(description='Xem trước')
    def image_thumb_large(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:240px;max-height:240px;object-fit:contain;border-radius:8px;border:1px solid #ddd;" />',
                obj.image.url,
            )
        return '—'

    @admin.display(description='Số thiết bị', ordering='_device_count')
    def device_count(self, obj):
        return obj._device_count


@admin.register(PhotoboothDevice)
class PhotoboothDeviceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'device_id',
        'address',
        'filter_count',
        'background_count',
        'decor_frame_count',
        'is_active',
        'last_seen_at',
        'created_at',
    )
    list_filter = ('is_active',)
    search_fields = ('name', 'device_id', 'address', 'notes')
    ordering = ('-id',)
    filter_horizontal = ('filters', 'backgrounds', 'decor_frames')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _filter_count=Count('filters', distinct=True),
            _background_count=Count('backgrounds', distinct=True),
            _decor_frame_count=Count('decor_frames', distinct=True),
        )

    @admin.display(description='Filters', ordering='_filter_count')
    def filter_count(self, obj):
        return obj._filter_count

    @admin.display(description='BG', ordering='_background_count')
    def background_count(self, obj):
        return obj._background_count

    @admin.display(description='Khung', ordering='_decor_frame_count')
    def decor_frame_count(self, obj):
        return obj._decor_frame_count

    fieldsets = (
        (None, {'fields': ('device_id', 'name', 'is_active')}),
        (
            'Địa chỉ & thông tin (tùy chọn)',
            {'fields': ('address', 'notes'), 'classes': ('wide',)},
        ),
        (
            'Filter, background & khung trang trí cho booth này',
            {'fields': ('filters', 'backgrounds', 'decor_frames')},
        ),
        ('Hệ thống', {'fields': ('last_seen_at', 'created_at', 'updated_at')}),
    )
    readonly_fields = ('last_seen_at', 'created_at', 'updated_at')


@admin.register(PaymentOrder)
class PaymentOrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'txn_ref',
        'amount_vnd',
        'status',
        'capture_package',
        'booth_id',
        'vnp_transaction_no',
        'expires_at',
        'paid_at',
        'created_at',
    )
    list_filter = ('status', 'capture_package')
    search_fields = ('txn_ref', 'vnp_transaction_no', 'booth_id')
    autocomplete_fields = ('capture_package',)
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-id',)
    fieldsets = (
        (
            'Đơn VNPAY',
            {
                'fields': (
                    'txn_ref',
                    'amount_vnd',
                    'status',
                    'expires_at',
                    'paid_at',
                ),
            },
        ),
        (
            'Gói chụp gắn với đơn',
            {
                'description': 'Mỗi đơn thanh toán gắn với đúng một gói chụp đã chọn trên booth.',
                'fields': ('capture_package',),
            },
        ),
        (
            'Booth & VNPAY',
            {
                'fields': (
                    'booth_id',
                    'vnp_transaction_no',
                    'vnp_response_code',
                    'vnp_transaction_status',
                ),
            },
        ),
        ('Hệ thống', {'fields': ('created_at', 'updated_at')}),
    )

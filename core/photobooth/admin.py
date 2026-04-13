from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html

from core.photobooth.models import (
    CapturePackage,
    ImagePhotobooth,
    PaymentOrder,
    PhotoboothBackground,
    PhotoboothDecorFrame,
    PhotoboothDevice,
    PhotoboothFilter,
    PhotoboothSticker,
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


@admin.register(PhotoboothSticker)
class PhotoboothStickerAdmin(admin.ModelAdmin):
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
        'sticker_count',
        'is_active',
        'last_seen_at',
        'created_at',
    )
    list_filter = ('is_active',)
    search_fields = ('name', 'device_id', 'address', 'notes')
    ordering = ('-id',)
    filter_horizontal = ('filters', 'backgrounds', 'decor_frames', 'stickers')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _filter_count=Count('filters', distinct=True),
            _background_count=Count('backgrounds', distinct=True),
            _decor_frame_count=Count('decor_frames', distinct=True),
            _sticker_count=Count('stickers', distinct=True),
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

    @admin.display(description='Sticker', ordering='_sticker_count')
    def sticker_count(self, obj):
        return obj._sticker_count

    fieldsets = (
        (None, {'fields': ('device_id', 'name', 'is_active')}),
        (
            'Địa chỉ & thông tin (tùy chọn)',
            {'fields': ('address', 'notes'), 'classes': ('wide',)},
        ),
        (
            'Filter, background, khung & sticker cho booth này',
            {'fields': ('filters', 'backgrounds', 'decor_frames', 'stickers')},
        ),
        ('Hệ thống', {'fields': ('last_seen_at', 'created_at', 'updated_at')}),
    )
    readonly_fields = ('last_seen_at', 'created_at', 'updated_at')

    class PaymentOrderInline(admin.TabularInline):
        model = PaymentOrder
        fk_name = 'device'
        extra = 0
        fields = ('txn_ref', 'amount_vnd', 'status', 'capture_package', 'paid_at', 'created_at')
        readonly_fields = ('txn_ref', 'amount_vnd', 'status', 'capture_package', 'paid_at', 'created_at')
        show_change_link = True

    inlines = [PaymentOrderInline]


@admin.register(PaymentOrder)
class PaymentOrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'txn_ref',
        'amount_vnd',
        'status',
        'capture_package',
        'device',
        'booth_id',
        'image_count',
        'payos_order_code',
        'payos_payment_link_id',
        'expires_at',
        'paid_at',
        'created_at',
    )
    list_filter = ('status', 'capture_package', 'device')
    search_fields = ('txn_ref', 'booth_id', 'payos_payment_link_id', 'payos_order_code', 'device__device_id', 'device__name')
    autocomplete_fields = ('capture_package', 'device')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-id',)

    class ImageInline(admin.TabularInline):
        model = ImagePhotobooth
        extra = 0
        readonly_fields = ('image_thumb', 'round_index', 'photo_index', 'created_at')
        fields = ('image_thumb', 'image', 'round_index', 'photo_index', 'created_at')

        @admin.display(description='Xem trước')
        def image_thumb(self, obj):
            if obj.image:
                return format_html(
                    '<img src="{}" width="80" height="80" alt="" '
                    'style="object-fit:cover;border-radius:4px;border:1px solid #ddd;" />',
                    obj.image.url,
                )
            return '—'

    inlines = [ImageInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_image_count=Count('images', distinct=True))

    @admin.display(description='Ảnh', ordering='_image_count')
    def image_count(self, obj):
        return obj._image_count
    fieldsets = (
        (
            'Đơn thanh toán',
            {
                'fields': (
                    'txn_ref',
                    'amount_vnd',
                    'status',
                    'payos_order_code',
                    'payos_payment_link_id',
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
            'Thiết bị',
            {
                'fields': ('device',),
            },
        ),
        (
            'Booth',
            {
                'fields': ('booth_id',),
            },
        ),
        ('Hệ thống', {'fields': ('created_at', 'updated_at')}),
    )


@admin.register(ImagePhotobooth)
class ImagePhotoboothAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'image_thumb',
        'payment_order',
        'round_index',
        'photo_index',
        'created_at',
    )
    list_filter = ('round_index',)
    search_fields = ('payment_order__txn_ref',)
    autocomplete_fields = ('payment_order',)
    readonly_fields = ('image_thumb_large', 'created_at')
    ordering = ('-id',)
    fieldsets = (
        (None, {'fields': ('payment_order', 'image', 'image_thumb_large')}),
        ('Vị trí', {'fields': ('round_index', 'photo_index')}),
        ('Hệ thống', {'fields': ('created_at',)}),
    )

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
                '<img src="{}" style="max-width:320px;max-height:320px;object-fit:contain;border-radius:8px;border:1px solid #ddd;" />',
                obj.image.url,
            )
        return '—'

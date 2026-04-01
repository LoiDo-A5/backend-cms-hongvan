from django.contrib import admin

from core.photobooth.models import CapturePackage, PaymentOrder, PhotoboothDevice


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


@admin.register(PhotoboothDevice)
class PhotoboothDeviceAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'device_id',
        'is_active',
        'last_seen_at',
        'created_at',
    )
    list_filter = ('is_active',)
    search_fields = ('name', 'device_id')
    ordering = ('-id',)


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
    list_filter = ('status',)
    search_fields = ('txn_ref', 'vnp_transaction_no', 'booth_id')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-id',)

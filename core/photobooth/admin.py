from django.contrib import admin

from core.photobooth.models import CapturePackage


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

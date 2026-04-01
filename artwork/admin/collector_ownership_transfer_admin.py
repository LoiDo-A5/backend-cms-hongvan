from django.contrib import admin


class CollectorOwnershipTransferAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'transferrer',
        'transferee',
        'artwork',
        'certificate',
        'transferred_at',
    )
    list_filter = ('transferred_at',)
    search_fields = (
        'transferrer__name',
        'transferrer__email',
        'transferee__name',
        'transferee__email',
        'artwork__title',
        'artwork__inventory_code',
    )
    autocomplete_fields = (
        'transferrer',
        'transferee',
        'artwork',
        'certificate',
    )
    readonly_fields = ('transferred_at',)
    date_hierarchy = 'transferred_at'

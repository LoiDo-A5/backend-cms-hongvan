from django.contrib import admin


class ArtworkLogAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'artwork',
        'action_type',
        'user',
        'created_at',
    )
    list_filter = (
        'action_type',
        'created_at',
    )
    search_fields = (
        'artwork__title',
        'artwork__inventory_code',
        'content_en',
        'content_vi',
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

    def artwork_title(self, obj):
        return obj.artwork.title if obj.artwork else 'N/A'

    artwork_title.short_description = 'Artwork'
    artwork_title.admin_order_field = 'artwork__title'

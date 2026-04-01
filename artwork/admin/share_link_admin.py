from django.contrib import admin


class ShareLinkAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'user', 'title', 'share_type', 'recipient_type',
        'recipients_count', 'access_count', 'created_at', 'expires_at', 'artwork_count',
    )
    list_filter = ('share_type', 'recipient_type', 'is_active', 'expiration_type')
    search_fields = ('title', 'description', 'user__username')
    readonly_fields = ('id', 'created_at', 'updated_at', 'access_count', 'last_accessed_at')
    filter_horizontal = ('recipients', 'collections')

    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'user', 'title', 'description', 'banner'),
        }),
        ('Share Settings', {
            'fields': ('share_type', 'artwork', 'collections', 'recipient_type', 'recipients'),
        }),
        ('Security Settings', {
            'fields': ('password', 'is_active', 'expiration_type', 'expires_at'),
        }),
        ('Tracking', {
            'classes': ('collapse',),
            'fields': ('access_count', 'last_accessed_at', 'created_at', 'updated_at'),
        }),
        ('Advanced', {
            'classes': ('collapse',),
            'fields': (),
        }),
    )

    def artwork_count(self, obj):
        return obj.artwork.count()
    artwork_count.short_description = 'Artwork Count'

    def recipients_count(self, obj):
        return obj.recipients.count()
    recipients_count.short_description = 'Recipients'

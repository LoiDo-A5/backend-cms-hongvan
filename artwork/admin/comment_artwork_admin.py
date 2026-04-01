from django.contrib import admin


class CommentArtworkAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'artwork',
        'user',
        'is_hidden',
        'created_at',
    )
    list_filter = (
        'created_at',
        'is_hidden',
    )
    search_fields = (
        'artwork__title',
        'artwork__inventory_code',
        'user__username',
        'user__name',
        'content',
    )
    autocomplete_fields = (
        'artwork',
        'user',
    )
    list_editable = (
        'is_hidden',
    )
    readonly_fields = (
        'created_at',
    )
    date_hierarchy = 'created_at'
    readonly_fields = (
        'created_at',
    )

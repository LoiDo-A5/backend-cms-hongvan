from django.contrib import admin


class UserLogAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'action_type',
        'created_at',
    )
    list_filter = (
        'action_type',
        'created_at',
    )
    search_fields = (
        'user__id',
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

from django.contrib import admin


class UserSignalIdAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
    )

    search_fields = ['user__username']
    autocomplete_fields = ['user']

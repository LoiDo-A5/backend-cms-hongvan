from django.contrib import admin


class SavedUserAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
    )

    search_fields = ['user__legal_name']
    autocomplete_fields = ['user', 'saved_user']

from django.contrib import admin


class CollectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'uuid', 'title', 'owner', 'is_public', 'created_at', 'updated_at')
    list_filter = ('owner',)
    search_fields = ('title', 'owner__name')
    ordering = ('-created_at',)
    filter_horizontal = ('artworks',)
    autocomplete_fields = ['owner']

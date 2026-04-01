from django.contrib import admin


class ArtworkEditionAdmin(admin.ModelAdmin):
    list_display = ('id', 'artwork', 'edition_number', 'location')
    list_filter = ('artwork',)
    search_fields = ('artwork__title', 'edition_number', 'location__location', 'id')
    autocomplete_fields = ['location']

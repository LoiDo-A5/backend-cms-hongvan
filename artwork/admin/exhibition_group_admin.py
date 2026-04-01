from django.contrib import admin


class ExhibitionGroupAdmin(admin.ModelAdmin):
    list_display = ('title', 'description')
    search_fields = ('title', 'description')
    list_filter = ('artworks',)

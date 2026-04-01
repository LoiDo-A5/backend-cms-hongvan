from django.contrib import admin


class SizeArtworkAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'length', 'width', 'depth', 'weight')
    list_filter = ('category',)
    search_fields = ('name',)

from django.contrib import admin


class LikeCollectionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'collection')
    list_filter = ('user', 'collection')
    search_fields = ('id', 'user', 'collection')

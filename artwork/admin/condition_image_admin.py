from django.contrib import admin

from artwork.models import ConditionImageBatch, ConditionImage


class ConditionImageInline(admin.TabularInline):
    model = ConditionImage
    extra = 0
    readonly_fields = ('image', 'order')


@admin.register(ConditionImageBatch)
class ConditionImageBatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'artwork', 'owner', 'created_at')
    search_fields = ('artwork__title', 'owner__name', 'owner__email')
    autocomplete_fields = ('artwork', 'owner')
    inlines = [ConditionImageInline]


@admin.register(ConditionImage)
class ConditionImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'batch', 'order', 'image')
    autocomplete_fields = ('batch',)

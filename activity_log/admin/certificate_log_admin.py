from django.contrib import admin


class CertificateLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'data')
    list_filter = ('user',)
    search_fields = ('user',)
    autocomplete_fields = ['user']

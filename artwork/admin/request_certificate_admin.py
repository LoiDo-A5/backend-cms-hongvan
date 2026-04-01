from django.contrib import admin


class CertificateRequestAdmin(admin.ModelAdmin):
    list_display = ('artwork_edition', 'request_by', 'request_to', 'status')
    list_filter = ('request_by',)
    search_fields = ('request_by',)

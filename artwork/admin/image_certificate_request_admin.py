from django.contrib import admin


class ImageCertificateRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'certificate_request', 'image')
    list_filter = ('certificate_request',)
    search_fields = ('certificate_request__artwork_edition__artwork__title',)

from django.contrib import admin


class ShippingCertificateAdmin(admin.ModelAdmin):
    list_display = ('id', 'certificate', 'recipient', 'address', 'phone_number', 'created_at')
    search_fields = ('recipient', 'phone_number', 'address')
    readonly_fields = ('created_at',)

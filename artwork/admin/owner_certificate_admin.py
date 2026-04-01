from django.contrib import admin


class OwnerCertificateAdmin(admin.ModelAdmin):
    list_display = ('id', 'certificate', 'name', 'year_of_birth', 'address')
    list_filter = ('name',)
    search_fields = ('name',)

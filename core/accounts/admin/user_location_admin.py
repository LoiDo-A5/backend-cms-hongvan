from django.contrib import admin


class UserLocationAdmin(admin.ModelAdmin):
    search_fields = ['location']

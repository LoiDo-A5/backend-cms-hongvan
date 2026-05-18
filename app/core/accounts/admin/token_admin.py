from rest_framework.authtoken.admin import TokenAdmin


class FilterTokenAdmin(TokenAdmin):
    search_fields = ['user__username', 'user__phone_number']

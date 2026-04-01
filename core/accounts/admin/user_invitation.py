from django.contrib import admin
from django.utils.translation import gettext_lazy as _


class RecipientActivatedFilter(admin.SimpleListFilter):
    title = _('recipient activated')
    parameter_name = 'recipient_activated'

    def lookups(self, request, model_admin):
        return (
            ('Yes', _('Yes')),
            ('No', _('No')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'Yes':
            return queryset.filter(recipient__has_activated=True)
        if self.value() == 'No':
            return queryset.filter(recipient__has_activated=False)


class UserInvitationAdmin(admin.ModelAdmin):
    list_display = ('id', 'sender', 'recipient', 'recipient_has_activated', 'created_at')
    list_filter = [RecipientActivatedFilter]
    search_fields = ('email', 'sender__name', 'recipient__name')
    readonly_fields = ('created_at',)

    def recipient_has_activated(self, obj):
        return obj.recipient.has_activated

    recipient_has_activated.boolean = True
    recipient_has_activated.short_description = 'Recipient Activated'

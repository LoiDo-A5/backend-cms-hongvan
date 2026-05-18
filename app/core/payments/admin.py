from django.contrib import admin
from core.payments.models import PaymentOrder


@admin.register(PaymentOrder)
class PaymentOrderAdmin(admin.ModelAdmin):
    list_display = ('txn_ref', 'amount_vnd', 'payment_method', 'status', 'created_at', 'paid_at')
    list_filter = ('status', 'payment_method')
    search_fields = ('txn_ref', 'description')
    readonly_fields = ('created_at', 'updated_at', 'paid_at')
    ordering = ('-id',)

from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjUserAdmin
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.forms import UserCreationForm
from django.core.mail import send_mail
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from onesignal_sdk.client import Client
from onesignal_sdk.client import basic_auth_request
from onesignal_sdk.error import OneSignalHTTPError

from core.accounts.models import UserSignalId
from core.accounts.models import UserLocation
from core.accounts.tasks.sms import send_sms
from core.accounts.utils import login_content_generator
from core.accounts.utils import otp_generator


def send_test_sms(modeladmin, request, queryset):
    for user in queryset:
        otp = otp_generator()
        send_sms(user.phone_number, login_content_generator(otp, settings.SMS_OPT_TIMEOUT))
    messages.success(request, 'Sent.')


def send_test_email(modeladmin, request, queryset):
    for user in queryset:
        send_mail(
            'Test send email', f'{user.display_name} send email to you.',
            settings.EMAIL_SENDER, [user.email], fail_silently=False,
        )
    messages.success(request, 'Email sent.')


def send_test_notification(modeladmin, request, queryset):
    today = timezone.now()
    for user in queryset:
        user.send_notification(title='Test send notification', message=f'This is content testing {today}')
    messages.success(request, 'Notification sent.')


class CustomUserChangeForm(UserChangeForm):
    phone_number = forms.CharField(max_length=50, required=False)

    class Meta(UserChangeForm.Meta):
        model = get_user_model()


class CustomUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True

    class Meta(UserCreationForm.Meta):
        model = get_user_model()


class SignalIdInline(admin.TabularInline):
    model = UserSignalId
    extra = 0


class ExtendedClient(Client):
    def delete_player(self, player_id):
        return basic_auth_request(**self._kwargs_delete_player(player_id))

    def _kwargs_delete_player(self, player_id):
        return {
            'method': 'DELETE',
            'url': self._get_path(f'/players/{player_id}'),
            'token': self.rest_api_key,
            'params': {'app_id': self.app_id},
        }


def delete_one_signal_player_id(player_id):
    onesignal_client = ExtendedClient(
        rest_api_key=settings.ONESIGNAL_APP_KEY,
        app_id=settings.ONESIGNAL_APP_ID,
    )
    return onesignal_client.delete_player(player_id)


class UserLocationInline(admin.StackedInline):
    model = UserLocation
    can_delete = True
    verbose_name_plural = 'User location'
    fields = ('user', 'location')
    show_change_link = True


class UserAdmin(DjUserAdmin):
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    list_display = (
        'id',
        'uuid',
        'username',
        'phone_number',
        'email',
        'referred_by',
        'date_joined',
        'is_first_login',
    )
    autocomplete_fields = ['referred_by']

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (
            _('Personal info'), {
                'fields': (
                    'name',
                    'email',
                    'phone_number',
                    'birthday',
                    'is_phone_verified',
                    'time_zone',
                    'last_seen_notification_at',
                    'gender',
                    'avatar',
                    'background',
                    'role',
                    'has_activated',
                    'legal_name',
                    'year_of_birth',
                    'place_of_birth',
                    'is_first_login',
                    'uuid',
                    'uuid_last_updated_at',
                ),
            },
        ),
        (
            _('Referral'), {
                'fields': (
                    'referral_code',
                    'referred_by',
                ),
            },
        ),
        (
            _('Permissions'), {
                'fields': (
                    'is_active',
                    'is_staff',
                    'is_superuser',
                    'groups',
                    'user_permissions',
                ),
            },
        ),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    readonly_fields = ('uuid_last_updated_at',)
    ordering = ['-id']
    search_fields = ('username', 'email', 'phone_number', 'name', 'legal_name')
    add_fieldsets = (
        (
            None, {
                'classes': ('wide',),
                'fields': (
                    'username',
                    'name',
                    'email',
                    'password1',
                    'password2',
                ),
            },
        ),
    )
    actions = [
        'clear_one_signal_id',
    ]
    inlines = [
        UserLocationInline,
        SignalIdInline,
    ]
    list_filter = (
        'date_joined',
        'is_active',
        'is_staff',
        'is_superuser',
        'is_first_login',
    )

    def clear_one_signal_id(self, request, queryset):
        for user_signal_id in UserSignalId.objects.filter(user__in=queryset):
            user_signal_id.delete()
            try:
                delete_one_signal_player_id(user_signal_id.signal_id)
            except OneSignalHTTPError:
                pass
        messages.success(request, "Users' one signal id is delete.")

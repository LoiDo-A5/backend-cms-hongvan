from django import forms
from django.contrib.auth import views as auth_views
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy


class LoginForm(AuthenticationForm):
    remember_me = forms.BooleanField(label=gettext_lazy('Remember Me'), initial=True, required=False)

    error_messages = {
        **AuthenticationForm.error_messages,
        'phone_need_verify': gettext_lazy('Please verify phone number'),
    }

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_phone_verified:
            raise ValidationError(
                self.error_messages['phone_need_verify'],
                code='phone_need_verify',
            )


class LoginView(auth_views.LoginView):
    authentication_form = LoginForm
    redirect_field_name = 'next'

    def form_valid(self, form):
        remember_me = form.cleaned_data['remember_me']
        if not remember_me:
            self.request.session.set_expiry(0)
            self.request.session.modified = True
        return super().form_valid(form)

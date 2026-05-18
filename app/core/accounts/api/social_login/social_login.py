from allauth.account import app_settings as allauth_settings
from allauth.socialaccount.helpers import complete_social_login
from dj_rest_auth.registration.serializers import SocialLoginSerializer
from dj_rest_auth.registration.views import SocialLoginView
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from requests.exceptions import HTTPError
from rest_framework import serializers

from common.api.ignore_throttle_on_test import IgnoreThrottleOnTestMixin
from core.accounts.api.user_api import UserSerializer


class CustomSocialLoginSerializer(SocialLoginSerializer):
    def get_social_login(self, *args, **kwargs):
        login = super().get_social_login(*args, **kwargs)
        if not login.email_addresses:
            raise serializers.ValidationError(_('Email address is required for social login'))

        self.login_obj = login  # store the login object
        login.user.is_using_social_avatar = True
        return login

    def validate(self, attrs):  # pragma: nocover we copy this from dj_rest_auth, custom from line 100
        view = self.context.get('view')
        request = self._get_request()

        if not view:
            raise serializers.ValidationError(
                _('View is not defined, pass it as a context variable'),
            )

        adapter_class = getattr(view, 'adapter_class', None)
        if not adapter_class:
            raise serializers.ValidationError(_('Define adapter_class in view'))

        adapter = adapter_class(request)
        app = adapter.get_provider().get_app(request)

        # More info on code vs access_token
        # http://stackoverflow.com/questions/8666316/facebook-oauth-2-0-code-and-token

        access_token = attrs.get('access_token')
        code = attrs.get('code')
        # Case 1: We received the access_token
        if access_token:
            tokens_to_parse = {'access_token': access_token}
            token = access_token
            # For sign in with apple
            id_token = attrs.get('id_token')
            if id_token:
                tokens_to_parse['id_token'] = id_token

        # Case 2: We received the authorization code
        elif code:
            self.set_callback_url(view=view, adapter_class=adapter_class)
            self.client_class = getattr(view, 'client_class', None)

            if not self.client_class:
                raise serializers.ValidationError(
                    _('Define client_class in view'),
                )

            provider = adapter.get_provider()
            scope = provider.get_scope(request)
            client = self.client_class(
                request,
                app.client_id,
                app.secret,
                adapter.access_token_method,
                adapter.access_token_url,
                self.callback_url,
                scope,
                scope_delimiter=adapter.scope_delimiter,
                headers=adapter.headers,
                basic_auth=adapter.basic_auth,
            )
            token = client.get_access_token(code)
            access_token = token['access_token']
            tokens_to_parse = {'access_token': access_token}

            # If available we add additional data to the dictionary
            for key in ['refresh_token', 'id_token', adapter.expires_in_key]:
                if key in token:
                    tokens_to_parse[key] = token[key]
        else:
            raise serializers.ValidationError(
                _('Incorrect input. access_token or code is required.'),
            )

        social_token = adapter.parse_token(tokens_to_parse)
        social_token.app = app

        try:
            login = self.get_social_login(adapter, app, social_token, token)
            complete_social_login(request, login)
        except HTTPError:
            raise serializers.ValidationError(_('Incorrect value'))

        if not login.is_existing:  # EoH custom this
            # We have an account already signed up in a different flow
            # with the same email address: raise an exception.
            # This needs to be handled in the frontend. We can not just
            # link up the accounts due to security constraints
            filters = {'email': login.user.email}
            if not allauth_settings.UNIQUE_EMAIL:
                filters.update({'app_provider': request.app_provider})

            account_exists = get_user_model().objects.filter(**filters).exists()
            if account_exists:
                raise serializers.ValidationError(
                    _('Your email has been registered, please try again with another social login.'),
                )

            login.lookup()
            login.save(request, connect=True)

        attrs['user'] = login.account.user
        attrs['login'] = self.login_obj
        return attrs


class CustomLoginResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    token = serializers.CharField(source='key')


class SocialLoginApi(IgnoreThrottleOnTestMixin, SocialLoginView):
    serializer_class = CustomSocialLoginSerializer

    def process_login(self):
        super(SocialLoginApi, self).process_login()

        if not self.user.is_using_social_avatar:
            return

        login = self.serializer.validated_data['login']

        self.user.name = login.account.extra_data['name'] if 'name' in login.account.extra_data else None

        self.user.save()

    def get_response_serializer(self):
        return CustomLoginResponseSerializer

    def post(self, request, *args, **kwargs):
        self.request = request
        self.serializer = self.get_serializer(
            data=self.request.data,
        )
        self.serializer.is_valid(raise_exception=True)

        self.login()
        return self.get_response()

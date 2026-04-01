import logging

from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.utils.translation import gettext_lazy as _

from common.exceptions import BadRequest

logger = logging.getLogger(__name__)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def authentication_error(
            self,
            request,
            provider_id,
            error=None,
            exception=None,
            extra_context=None,
    ):
        if exception:
            logger.exception(exception)
        else:
            logger.exception('Fail to login social network')

        super(CustomSocialAccountAdapter, self).authentication_error(
            request=request,
            provider_id=provider_id,
            error=error,
            exception=exception,
            extra_context=extra_context,
        )

    def validate_disconnect(self, account, accounts):
        if len(accounts) == 1:
            user = account.user
            if not user.has_usable_password() or not user.phone_number or not user.is_phone_verified:
                raise BadRequest(_('Your account must be set up password and phone number'))

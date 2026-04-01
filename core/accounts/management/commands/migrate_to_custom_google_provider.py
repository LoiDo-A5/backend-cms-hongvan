from allauth.socialaccount.models import SocialAccount  # pragma: nocover
from allauth.socialaccount.models import SocialApp  # pragma: nocover
from django.core.management.base import BaseCommand  # pragma: nocover

from core.accounts.custom_providers.custom_google.provider import CustomGoogleProvider  # pragma: nocover


class Command(BaseCommand):  # pragma: nocover

    def handle(self, *args, **options):
        google_accounts = SocialAccount.objects.filter(provider='google', user__org_id__in=[1036, 1080, 1034])
        for account in google_accounts:
            if account.user.org_id == 1036:  # akia
                google_app_id = 199
            elif account.user.org_id == 1080:  # atlantis
                google_app_id = 134
            else:
                google_app_id = 34  # eoh

            account.uid = f'{google_app_id}-{account.uid}'
            account.save(update_fields=['uid', 'provider'])

        SocialApp.objects.filter(provider='google').update(provider=CustomGoogleProvider.id)

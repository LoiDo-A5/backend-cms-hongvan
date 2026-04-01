from allauth.socialaccount import providers
from allauth.socialaccount.providers.google.provider import GoogleProvider


class CustomGoogleProvider(GoogleProvider):
    id = 'custom_google'
    name = 'Custom Google'

    def extract_uid(self, data):
        social_app = self.get_app(self.request)
        return f'{social_app.id}-{str(data["id"])}'


providers.registry.register(CustomGoogleProvider)

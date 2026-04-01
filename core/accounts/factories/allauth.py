import factory
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

from common.tests.factory_base import FactoryBase


class SocialAppFactory(FactoryBase):
    class Meta:
        model = SocialApp

    provider = 'facebook'
    name = 'facebook login'
    client_id = 'client_id'
    secret = 'secret'
    key = 'key'
    sites = [1]

    @factory.post_generation
    def sites(self, create, extracted, **kwargs):  # noqa: F811
        for site in extracted:
            self.sites.add(site)


class SiteFactory(FactoryBase):
    class Meta:
        model = Site
        django_get_or_create = ('domain',)

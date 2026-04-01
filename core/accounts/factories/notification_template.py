import factory
from common.tests.factory_base import FactoryBase

from core.accounts.models import NotificationTemplate


class NotificationTemplateFactory(FactoryBase):
    class Meta:
        model = NotificationTemplate

    title_vi = factory.Faker('sentence', nb_words=3)
    title_en = factory.Faker('sentence', nb_words=3)
    content_en = factory.Faker('sentence', nb_words=10)
    content_vi = factory.Faker('sentence', nb_words=10)
    redirect = '/home'

import factory

from common.tests.factory_base import FactoryBase
from core.accounts.factories.user import UserAwardFactory
from core.accounts.models import ImageAward


class ImageAwardFactory(FactoryBase):
    class Meta:
        model = ImageAward

    award = factory.SubFactory(UserAwardFactory)
    image = factory.Faker('file_path', absolute=False)

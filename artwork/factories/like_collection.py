import factory

from artwork.factories.collection import CollectionFactory
from artwork.models import LikeCollection
from common.tests.factory_base import FactoryBase
from core.accounts.factories.user import UserFactory


class LikeCollectionFactory(FactoryBase):
    class Meta:
        model = LikeCollection

    user = factory.SubFactory(UserFactory)
    collection = factory.SubFactory(CollectionFactory)

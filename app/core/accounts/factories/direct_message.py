import factory

from common.tests.factory_base import FactoryBase
from core.accounts.models import DirectMessage
from core.accounts.factories.user import UserFactory


class DirectMessageFactory(FactoryBase):
    class Meta:
        model = DirectMessage

    sender = factory.SubFactory(UserFactory)
    receiver = factory.SubFactory(UserFactory)

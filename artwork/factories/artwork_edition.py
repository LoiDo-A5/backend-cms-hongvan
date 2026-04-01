import factory
import random

from artwork.factories.artwork import ArtworkFactory
from artwork.models.artwork_edition import ArtworkEdition
from artwork.utils.const import STATUS_CHOICES
from common.tests.factory_base import FactoryBase
from core.accounts.factories.user import UserLocationFactory


class ArtworkEditionFactory(FactoryBase):
    class Meta:
        model = ArtworkEdition

    artwork = factory.SubFactory(ArtworkFactory)
    edition_number = factory.Sequence(lambda n: n + 1)
    status = factory.LazyAttribute(lambda x: random.choice(STATUS_CHOICES)[0])
    location = factory.SubFactory(UserLocationFactory)

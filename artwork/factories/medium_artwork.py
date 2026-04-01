import factory

from artwork.utils.const import CATEGORY_CHOICES
from artwork.models import MediumArtwork
from common.tests.factory_base import FactoryBase


class MediumArtworkFactory(FactoryBase):
    class Meta:
        model = MediumArtwork

    name = factory.Sequence(lambda n: 'Medium %d' % n)
    category = factory.Faker('random_element', elements=[choice[0] for choice in CATEGORY_CHOICES])

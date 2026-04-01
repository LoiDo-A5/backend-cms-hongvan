import factory

from artwork.utils.const import CATEGORY_CHOICES
from artwork.models import StyleArtwork
from common.tests.factory_base import FactoryBase


class StyleArtworkFactory(FactoryBase):
    class Meta:
        model = StyleArtwork

    name = factory.Sequence(lambda n: 'Style %d' % n)
    category = factory.Faker('random_element', elements=[choice[0] for choice in CATEGORY_CHOICES])

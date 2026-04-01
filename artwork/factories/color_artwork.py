import factory

from artwork.utils.const import CATEGORY_CHOICES
from artwork.models import ColorArtwork
from common.tests.factory_base import FactoryBase


class ColorArtworkFactory(FactoryBase):
    class Meta:
        model = ColorArtwork

    name = factory.Sequence(lambda n: 'Color %d' % n)
    category = factory.Faker('random_element', elements=[choice[0] for choice in CATEGORY_CHOICES])

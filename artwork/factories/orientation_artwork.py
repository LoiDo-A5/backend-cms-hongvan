import factory

from artwork.utils.const import CATEGORY_CHOICES
from artwork.models import OrientationArtwork
from common.tests.factory_base import FactoryBase


class OrientationArtworkFactory(FactoryBase):
    class Meta:
        model = OrientationArtwork

    name = factory.Sequence(lambda n: 'Orientation %d' % n)
    category = factory.Faker('random_element', elements=[choice[0] for choice in CATEGORY_CHOICES])

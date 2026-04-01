import factory

from artwork.utils.const import CATEGORY_CHOICES
from artwork.models import SizeArtwork
from common.tests.factory_base import FactoryBase


class SizeArtworkFactory(FactoryBase):
    class Meta:
        model = SizeArtwork

    category = factory.Faker('random_element', elements=[choice[0] for choice in CATEGORY_CHOICES])
    length = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    width = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    depth = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    weight = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)

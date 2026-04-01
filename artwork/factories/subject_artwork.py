import factory

from artwork.utils.const import CATEGORY_CHOICES
from artwork.models import SubjectArtwork
from common.tests.factory_base import FactoryBase


class SubjectArtworkFactory(FactoryBase):
    class Meta:
        model = SubjectArtwork

    name = factory.Sequence(lambda n: 'Subject %d' % n)
    category = factory.Faker('random_element', elements=[choice[0] for choice in CATEGORY_CHOICES])

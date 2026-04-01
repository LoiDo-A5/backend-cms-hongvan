import uuid

import factory

from artwork.factories.artwork_artist import ArtworkArtistFactory
from artwork.factories.medium_artwork import MediumArtworkFactory
from artwork.factories.size_artwork import SizeArtworkFactory
from artwork.factories.style_artwork import StyleArtworkFactory
from artwork.factories.subject_artwork import SubjectArtworkFactory
from artwork.utils.const import CATEGORY_CHOICES
from artwork.models import ArtWork
from common.tests.factory_base import FactoryBase
from core.accounts.factories.user import UserFactory
from core.accounts.factories.user import UserLocationFactory


class ArtworkFactory(FactoryBase):
    class Meta:
        model = ArtWork

    uuid = factory.LazyFunction(uuid.uuid4)
    title = factory.Sequence(lambda n: 'ArtWork %d' % n)
    artist_artwork = factory.SubFactory(ArtworkArtistFactory)
    owner = factory.SubFactory(UserFactory)
    category = factory.Faker('random_element', elements=[choice[0] for choice in CATEGORY_CHOICES])
    size = factory.SubFactory(SizeArtworkFactory)
    status = 'available'
    location = factory.SubFactory(UserLocationFactory)
    style = factory.SubFactory(StyleArtworkFactory)
    medium = factory.SubFactory(MediumArtworkFactory)
    is_public = True
    year_created = factory.Faker('year')
    subject = factory.SubFactory(SubjectArtworkFactory)

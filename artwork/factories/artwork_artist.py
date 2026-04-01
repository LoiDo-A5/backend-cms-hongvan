import factory

from artwork.models import ArtworkArtist
from common.tests.factory_base import FactoryBase
from core.accounts.factories.user import UserFactory


class ArtworkArtistFactory(FactoryBase):
    class Meta:
        model = ArtworkArtist

    artist_name = factory.Faker('name')
    contact_info = factory.Faker('email')
    year_of_birth = factory.Faker('random_int', min=1900, max=2025)
    year_of_death = factory.Faker('random_int', min=1900, max=2025)
    create_user = factory.SubFactory(UserFactory)

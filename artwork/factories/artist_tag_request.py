import factory

from artwork.factories.artwork import ArtworkFactory

from artwork.models import ArtistTagRequest
from common.tests.factory_base import FactoryBase
from core.accounts.factories.user import UserFactory


class ArtistTagRequestFactory(FactoryBase):
    class Meta:
        model = ArtistTagRequest

    artwork = factory.SubFactory(ArtworkFactory)
    request_by = factory.SubFactory(UserFactory)
    request_to = factory.SubFactory(UserFactory)

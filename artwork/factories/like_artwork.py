import factory

from artwork.factories.artwork import ArtworkFactory
from artwork.models import LikeArtwork
from common.tests.factory_base import FactoryBase
from core.accounts.factories.user import UserFactory


class LikeArtworkFactory(FactoryBase):
    class Meta:
        model = LikeArtwork

    user = factory.SubFactory(UserFactory)
    artwork = factory.SubFactory(ArtworkFactory)

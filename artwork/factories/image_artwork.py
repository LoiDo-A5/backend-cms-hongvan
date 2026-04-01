import factory

from artwork.models import ImageArtwork
from artwork.factories.artwork import ArtworkFactory

from common.tests.factory_base import FactoryBase


class ImageArtworkFactory(FactoryBase):
    class Meta:
        model = ImageArtwork

    artwork = factory.SubFactory(ArtworkFactory)
    image = factory.Faker('file_path', absolute=False)

import factory

from artwork.factories.artwork import ArtworkFactory
from artwork.models import Collection
from common.tests.factory_base import FactoryBase
from core.accounts.factories.user import UserFactory


class CollectionFactory(FactoryBase):
    class Meta:
        model = Collection

    title = factory.Sequence(lambda n: 'ArtWork %d' % n)
    owner = factory.SubFactory(UserFactory)

    @factory.post_generation
    def artworks(self, create, extracted, **kwargs):
        if not create:
            return

        artworks = extracted or [ArtworkFactory()]
        for artwork in artworks:
            self.artworks.add(artwork)

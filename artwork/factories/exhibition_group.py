import factory
from faker import Faker

from artwork.factories.artwork import ArtworkFactory
from artwork.factories.exhibition import ExhibitionFactory
from artwork.models import ExhibitionGroup

fake = Faker()


class ExhibitionGroupFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ExhibitionGroup

    title = factory.Faker('word')
    description = factory.Faker('text', max_nb_chars=500)
    exhibition = factory.SubFactory(ExhibitionFactory)

    @factory.post_generation
    def artworks(self, create, extracted, **kwargs):
        if not create:
            return
        artworks = extracted or [ArtworkFactory()]
        for artwork in artworks:
            self.artworks.add(artwork)

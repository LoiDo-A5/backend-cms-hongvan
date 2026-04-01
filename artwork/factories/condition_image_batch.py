import factory
from common.tests.factory_base import FactoryBase
from core.accounts.factories.user import UserFactory
from artwork.factories.artwork import ArtworkFactory
from artwork.models import ConditionImageBatch, ConditionImage, ConditionImageBatchLog


class ConditionImageBatchFactory(FactoryBase):
    class Meta:
        model = ConditionImageBatch

    artwork = factory.SubFactory(ArtworkFactory)
    owner = factory.SubFactory(UserFactory)


class ConditionImageFactory(FactoryBase):
    class Meta:
        model = ConditionImage

    batch = factory.SubFactory(ConditionImageBatchFactory)
    image = factory.django.ImageField()
    order = factory.Sequence(int)


class ConditionImageBatchLogFactory(FactoryBase):
    class Meta:
        model = ConditionImageBatchLog

    batch = factory.SubFactory(ConditionImageBatchFactory)
    artwork = factory.SelfAttribute('batch.artwork')
    actor = factory.SubFactory(UserFactory)
    images_snapshot = factory.List(['image1.png', 'image2.png'])

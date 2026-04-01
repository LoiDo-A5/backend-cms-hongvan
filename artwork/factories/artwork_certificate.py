import factory

from artwork.factories.artwork_edition import ArtworkEditionFactory
from artwork.models import ArtworkCertificate
from common.tests.factory_base import FactoryBase
from core.accounts.factories.user import UserFactory
import uuid


class ArtworkCertificateFactory(FactoryBase):
    class Meta:
        model = ArtworkCertificate

    artwork_edition = factory.SubFactory(ArtworkEditionFactory)
    issued_by = factory.SubFactory(UserFactory)
    code = factory.LazyFunction(uuid.uuid4)
    signature = factory.Faker('file_path', absolute=False)

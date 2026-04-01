import factory

from artwork.models import OwnerCertificate

from common.tests.factory_base import FactoryBase
from artwork.factories.artwork_certificate import ArtworkCertificateFactory


class OwnerCertificateFactory(FactoryBase):
    class Meta:
        model = OwnerCertificate

    certificate = factory.SubFactory(ArtworkCertificateFactory)
    name = factory.Faker('name')
    year_of_birth = factory.Faker('pyint', min_value=1900, max_value=2022)
    address = factory.Faker('address')

import factory

from artwork.factories.artwork_edition import ArtworkEditionFactory
from artwork.models import CertificateRequest
from common.tests.factory_base import FactoryBase
from core.accounts.factories.user import UserFactory


class CertificateRequestFactory(FactoryBase):
    class Meta:
        model = CertificateRequest

    artwork_edition = factory.SubFactory(ArtworkEditionFactory)
    request_by = factory.SubFactory(UserFactory)
    request_to = factory.SubFactory(UserFactory)

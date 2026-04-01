import factory

from artwork.factories.certificate_request import CertificateRequestFactory
from artwork.models import ImageCertificateRequest
from common.tests.factory_base import FactoryBase


class ImageCertificateRequestFactory(FactoryBase):
    class Meta:
        model = ImageCertificateRequest

    certificate_request = factory.SubFactory(CertificateRequestFactory)
    image = factory.Faker('file_path', absolute=False)

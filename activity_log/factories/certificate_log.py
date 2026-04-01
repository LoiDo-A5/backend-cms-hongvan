import factory

from activity_log.models import CertificateLog
from artwork.factories.artwork_certificate import ArtworkCertificateFactory
from core.accounts.factories.user import UserFactory


class CertificateLogFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CertificateLog

    user = factory.SubFactory(UserFactory)
    certificate = factory.SubFactory(ArtworkCertificateFactory)
    data = factory.Faker('text', max_nb_chars=255)
    created_at = factory.Faker('date_time_this_decade')
    image = factory.django.ImageField(filename='certificate_log.jpg')

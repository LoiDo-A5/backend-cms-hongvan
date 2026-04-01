import factory
from datetime import timedelta
from django.utils import timezone
import random

from artwork.models import Exhibition
from artwork.utils.const import EXHIBITION_TYPE_CHOICES
from core.accounts.factories.user import UserFactory


class ExhibitionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Exhibition

    title = factory.Sequence(lambda n: 'Exhibition %d' % n)
    date_start = factory.LazyAttribute(lambda x: timezone.now() + timedelta(days=random.randint(1, 30)))
    date_end = factory.LazyAttribute(lambda x: x.date_start + timedelta(days=random.randint(1, 7)))
    address = factory.Faker('address')
    event_type = factory.Faker('random_element', elements=[choice[0] for choice in EXHIBITION_TYPE_CHOICES])
    cover_image = factory.Faker('image_url')
    preface = factory.Faker('text', max_nb_chars=6000)
    organizer_name = factory.Faker('company')
    owner = factory.SubFactory(UserFactory)

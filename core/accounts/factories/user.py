import factory
from common.tests.factory_base import FactoryBase
from faker import Faker

from core.accounts.models import User, UserProfile, UserSignalId
from core.accounts.models.user import USER_ROLE

faker = Faker()


class UserFactory(FactoryBase):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'email{n}@example.com')
    birthday = factory.Faker('date')
    phone_number = factory.Sequence(lambda n: str(n).zfill(10))
    is_phone_verified = True
    email = factory.Sequence(lambda n: f'email{n}@example.com')
    name = factory.Faker('name')
    legal_name = factory.Faker('name')
    password = factory.Faker('password')
    time_zone = 'Asia/Ho_Chi_Minh'
    role = USER_ROLE.USER
    has_activated = False

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        user = super(UserFactory, cls)._create(model_class, *args, **kwargs)
        password = kwargs['password']
        user.set_password(password)
        user.raw_password = password
        user.save()
        return user


class UserSignalIdFactory(FactoryBase):
    class Meta:
        model = UserSignalId

    user = factory.SubFactory(UserFactory)
    signal_id = factory.Faker('uuid4')


class UserProfileFactory(FactoryBase):
    class Meta:
        model = UserProfile

    user = factory.SubFactory(UserFactory)
    nick_name = factory.Faker('first_name')
    id_card_number = factory.Faker('ssn')
    address = factory.Faker('address')
    bio = factory.Faker('text', max_nb_chars=200)

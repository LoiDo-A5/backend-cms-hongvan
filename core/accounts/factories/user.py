import factory
from common.tests.factory_base import FactoryBase
from faker import Faker

from core.accounts.models import User, SavedUser, UserCollection
from core.accounts.models import UserGroupExhibition
from core.accounts.models import UserPublication
from core.accounts.models import UserLocation
from core.accounts.models import UserAward
from core.accounts.models import UserSignalId
from core.accounts.models import UserProfile
from core.accounts.models import UserSoloExhibition
from core.accounts.models.user import USER_ROLE
from core.accounts.models import UserVisibleSetting

faker = Faker()


class UserFactory(FactoryBase):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'email{n}@eoh.io')
    birthday = factory.Faker('date')
    phone_number = factory.Sequence(lambda n: str(n).zfill(10))
    is_phone_verified = True
    email = factory.Sequence(lambda n: f'email{n}@eoh.io')
    name = factory.Faker('name')
    legal_name = factory.Faker('name')
    password = factory.Faker('password')
    time_zone = 'Asia/Ho_Chi_Minh'
    role = USER_ROLE.COLLECTOR
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
    certification = factory.Faker('word')
    introduction = factory.Faker('text', max_nb_chars=500)
    signature = factory.Faker('file_path', absolute=False)


class UserVisibleSettingFactory(FactoryBase):
    class Meta:
        model = UserVisibleSetting

    user = factory.SubFactory(UserFactory)


class UserLocationFactory(FactoryBase):
    class Meta:
        model = UserLocation

    user = factory.SubFactory(UserFactory)
    location = factory.Faker('address')


class UserAwardFactory(FactoryBase):
    class Meta:
        model = UserAward

    user = factory.SubFactory(UserFactory)
    year = factory.Faker('year')
    description = factory.Faker('text', max_nb_chars=200)
    is_public = True


class UserSoloExhibitionFactory(FactoryBase):
    class Meta:
        model = UserSoloExhibition

    user = factory.SubFactory(UserFactory)
    year = factory.Faker('year')
    description = factory.Faker('text', max_nb_chars=200)
    is_public = True
    exhibition_link = factory.Faker('uri')


class UserGroupExhibitionFactory(FactoryBase):
    class Meta:
        model = UserGroupExhibition

    user = factory.SubFactory(UserFactory)
    year = factory.Faker('year')
    description = factory.Faker('text', max_nb_chars=200)
    is_public = True
    exhibition_link = factory.Faker('uri')


class UserPublicationFactory(FactoryBase):
    class Meta:
        model = UserPublication

    user = factory.SubFactory(UserFactory)
    year = factory.Faker('year')
    description = factory.Faker('text', max_nb_chars=200)
    is_public = True


class UserCollectionFactory(FactoryBase):
    class Meta:
        model = UserCollection

    user = factory.SubFactory(UserFactory)
    name = factory.Faker('text', max_nb_chars=10)
    is_public = True


class SavedUserFactory(FactoryBase):
    class Meta:
        model = SavedUser

    user = factory.SubFactory(UserFactory)
    saved_user = factory.SubFactory(UserFactory)

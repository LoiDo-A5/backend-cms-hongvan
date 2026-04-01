from factory import Faker, SubFactory, Sequence, Iterator
from factory.django import DjangoModelFactory

from artwork.models import ShareLink
from core.accounts.factories.user import UserFactory


class ShareLinkFactory(DjangoModelFactory):
    class Meta:
        model = ShareLink

    user = SubFactory(UserFactory)
    title = Sequence(lambda n: f'Share Link {n}')
    description = Faker('text', max_nb_chars=200)
    share_type = Iterator(['artwork', 'exhibition', 'mixed'])
    recipient_type = Iterator(['public', 'specific', 'both'])
    expiration_type = Iterator(['never', 'custom'])
    password = None
    expires_at = None
    is_active = True

    @classmethod
    def create_with_artwork(cls, user=None, artwork=None, **kwargs):
        """Create ShareLink with specific artwork"""
        if user is None:
            user = UserFactory()
        if artwork is None:
            from artwork.factories.artwork import ArtworkFactory
            artwork = ArtworkFactory(owner=user)

        share_link = cls.create(
            user=user,
            share_type='artwork',
            **kwargs,
        )
        share_link.artwork.add(artwork)
        return share_link

    @classmethod
    def create_with_exhibition(cls, user=None, exhibition=None, **kwargs):
        """Create ShareLink with specific exhibition"""
        if user is None:
            user = UserFactory()
        if exhibition is None:
            from artwork.factories.exhibition import ExhibitionFactory
            exhibition = ExhibitionFactory(owner=user)

        share_link = cls.create(
            user=user,
            share_type='exhibition',
            **kwargs,
        )
        return share_link

    @classmethod
    def create_with_password(cls, user=None, password='secret123', **kwargs):
        """Create ShareLink with password protection"""
        if user is None:
            user = UserFactory()
        return cls.create(
            user=user,
            password=password,
            **kwargs,
        )

    @classmethod
    def create_with_expiration(cls, user=None, days=7, **kwargs):
        """Create ShareLink with expiration"""
        if user is None:
            user = UserFactory()
        from django.utils import timezone
        expires_at = timezone.now() + timezone.timedelta(days=days)
        return cls.create(
            user=user,
            expiration_type='custom',
            expires_at=expires_at,
            **kwargs,
        )

    @classmethod
    def create_expired(cls, user=None, **kwargs):
        """Create ShareLink that is expired"""
        if user is None:
            user = UserFactory()
        from django.utils import timezone
        expires_at = timezone.now() - timezone.timedelta(days=1)
        return cls.create(
            user=user,
            expiration_type='custom',
            expires_at=expires_at,
            **kwargs,
        )

    @classmethod
    def create_inactive(cls, user=None, **kwargs):
        """Create ShareLink that is inactive"""
        if user is None:
            user = UserFactory()
        return cls.create(
            user=user,
            is_active=False,
            **kwargs,
        )

    @classmethod
    def create_with_recipients(cls, user=None, recipients=None, **kwargs):
        """Create ShareLink with specific recipients"""
        if user is None:
            user = UserFactory()
        if recipients is None:
            recipients = [UserFactory(), UserFactory()]

        share_link = cls.create(user=user, **kwargs)
        for recipient in recipients:
            share_link.add_recipient(recipient)
        return share_link

    @classmethod
    def create_public_artwork_link(cls, user=None, **kwargs):
        """Create public artwork share link"""
        if user is None:
            user = UserFactory()
        return cls.create(
            user=user,
            share_type='artwork',
            recipient_type='public',
            **kwargs,
        )

    @classmethod
    def create_protected_exhibition_link(cls, user=None, **kwargs):
        """Create password-protected exhibition share link"""
        if user is None:
            user = UserFactory()
        return cls.create(
            user=user,
            share_type='exhibition',
            recipient_type='specific',
            password='protected123',
            **kwargs,
        )

    @classmethod
    def create_mixed_expiring_link(cls, user=None, **kwargs):
        """Create mixed content share link with expiration"""
        if user is None:
            user = UserFactory()
        from django.utils import timezone
        expires_at = timezone.now() + timezone.timedelta(hours=24)
        return cls.create(
            user=user,
            share_type='mixed',
            recipient_type='both',
            expiration_type='custom',
            expires_at=expires_at,
            password='mixed123',
            **kwargs,
        )

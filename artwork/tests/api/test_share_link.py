from django.utils import timezone
from datetime import timedelta
from rest_framework import status

from artwork.factories.artwork import ArtworkFactory
from artwork.factories.collection import CollectionFactory
from artwork.factories.exhibition import ExhibitionFactory
from artwork.factories.share_link import ShareLinkFactory
from artwork.models import ShareLink
from core.accounts.factories.user import UserFactory
from core.accounts.tests.api.base_user_test import BaseUserTest
from core.accounts.models.notification_template import NOTIFICATIONS_CONTENT_CODE
from core.accounts.models.notification import Notification

from rest_framework.test import APIRequestFactory

from artwork.api.share_link import ShareLinkViewSet


class ShareLinkViewSetTest(BaseUserTest):
    def setUp(self) -> None:
        super().setUp()
        self.artwork = ArtworkFactory(owner=self.user, is_public=True)
        self.exhibition = ExhibitionFactory(owner=self.user, is_public=True)

    def test_list_share_links(self):
        share_link1 = ShareLinkFactory(user=self.user)
        share_link1.artwork.add(self.artwork)
        share_link2 = ShareLinkFactory(user=self.user)
        share_link2.artwork.add(self.artwork)
        other_user = UserFactory()
        ShareLinkFactory(user=other_user)

        response = self.client.get('/api/artwork/share_links/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_share_link(self):
        share_link = ShareLinkFactory(
            user=self.user,
            title='Test Link',
        )
        share_link.artwork.add(self.artwork)

        response = self.client.get(f'/api/artwork/share_links/{share_link.id}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], 'Test Link')

    def test_create_share_link_artwork(self):
        data = {
            'title': 'New Share Link',
            'description': 'Test description',
            'artwork': [self.artwork.id],
            'share_type': 'artwork',
            'recipient_type': 'public',
            'expiration_type': 'never',
        }

        response = self.client.post('/api/artwork/share_links/', data=data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        share_link = ShareLink.objects.filter(id=response.data['id']).first()

        self.assertEqual(response.data['title'], 'New Share Link')
        self.assertIsNotNone(share_link)
        self.assertIn(self.artwork.id, list(share_link.artwork.values_list('id', flat=True)))

    def test_create_share_link_with_password(self):
        data = {
            'title': 'Protected Link',
            'artwork': [self.artwork.id],
            'share_type': 'artwork',
            'recipient_type': 'public',
            'expiration_type': 'never',
            'has_password': True,
            'password': 'secret123',
        }

        response = self.client.post('/api/artwork/share_links/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        share_link = ShareLink.objects.first()
        self.assertEqual(share_link.password, 'secret123')

    def test_create_share_link_with_expiration(self):
        expires_at = (timezone.now() + timedelta(days=7)).isoformat()
        data = {
            'title': 'Expiring Link',
            'artwork': [self.artwork.id],
            'share_type': 'artwork',
            'recipient_type': 'public',
            'expiration_type': 'custom',
            'has_expiration': True,
            'expires_at': expires_at,
        }

        response = self.client.post('/api/artwork/share_links/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNotNone(response.data['expires_at'])

    def test_create_share_link_with_recipients(self):
        recipient1 = UserFactory()
        recipient2 = UserFactory()
        data = {
            'title': 'Recipient Link',
            'artwork': [self.artwork.id],
            'share_type': 'artwork',
            'recipient_type': 'specific',
            'expiration_type': 'never',
            'recipient_user_ids': [recipient1.id, recipient2.id],
        }

        response = self.client.post('/api/artwork/share_links/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        share_link = ShareLink.objects.first()
        self.assertEqual(share_link.recipients.count(), 2)
        self.assertTrue(share_link.recipients.filter(id=recipient1.id).exists())
        self.assertTrue(share_link.recipients.filter(id=recipient2.id).exists())

    def test_create_share_link_share_all_without_artwork(self):
        user = UserFactory()
        data = {
            'title': 'Share All Link',
            'description': 'Share everything',
            'is_share_all': True,
            'recipient_type': 'specific',
            'expiration_type': 'never',
            'recipient_user_ids': [user.id],
            'share_type': 'mixed',
        }

        response = self.client.post('/api/artwork/share_links/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        share_link = ShareLink.objects.first()
        self.assertTrue(share_link.is_share_all)
        self.assertEqual(share_link.artwork.count(), 0)
        self.assertEqual(share_link.share_type, 'mixed')
        self.assertEqual(share_link.user, self.user)

    def test_create_share_link_collection_sets_only_owned_collections(self):
        owned_collection = CollectionFactory(owner=self.user)
        other_user = UserFactory()
        not_owned_collection = CollectionFactory(owner=other_user)

        data = {
            'title': 'Collection Share Link',
            'description': 'Share a collection',
            'share_type': 'collection',
            'recipient_type': 'public',
            'expiration_type': 'never',
            'is_share_all': True,
            'collection_ids': [owned_collection.id, not_owned_collection.id],
        }

        response = self.client.post('/api/artwork/share_links/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        share_link = ShareLink.objects.first()
        self.assertEqual(share_link.share_type, 'collection')
        self.assertEqual(list(share_link.collections.values_list('id', flat=True)), [owned_collection.id])

    def test_create_share_link_mixed_type_auto_detect(self):
        data = {
            'title': 'Mixed Link',
            'artwork': [self.artwork.id],
            'recipient_type': 'public',
            'expiration_type': 'never',
        }

        response = self.client.post('/api/artwork/share_links/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        share_link = ShareLink.objects.first()
        self.assertEqual(share_link.share_type, 'artwork')

    def test_create_share_link_empty_artwork_error(self):
        data = {
            'title': 'Empty Link',
            'artwork': [],
            'share_type': 'mixed',
            'recipient_type': 'public',
            'expiration_type': 'never',
        }

        response = self.client.post('/api/artwork/share_links/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_share_link_custom_expiration_without_date_error(self):
        data = {
            'title': 'Invalid Link',
            'artwork': [self.artwork.id],
            'share_type': 'artwork',
            'recipient_type': 'public',
            'expiration_type': 'custom',
        }

        response = self.client.post('/api/artwork/share_links/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_share_link_past_expiration_error(self):
        past_date = (timezone.now() - timedelta(days=1)).isoformat()
        data = {
            'title': 'Past Link',
            'artwork': [self.artwork.id],
            'share_type': 'artwork',
            'recipient_type': 'public',
            'expiration_type': 'custom',
            'expires_at': past_date,
        }

        response = self.client.post('/api/artwork/share_links/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_share_link(self):
        share_link = ShareLinkFactory(user=self.user, title='Old Title')

        response = self.client.patch(
            f'/api/artwork/share_links/{share_link.id}/',
            data={'title': 'New Title'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        share_link.refresh_from_db()
        self.assertEqual(share_link.title, 'New Title')

    def test_delete_share_link(self):
        share_link = ShareLinkFactory(user=self.user)

        response = self.client.delete(f'/api/artwork/share_links/{share_link.id}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ShareLink.objects.count(), 0)

    def test_create_share_link_with_title_uses_correct_notification(self):
        recipient = UserFactory()
        data = {
            'title': 'My Share Link',
            'artwork': [self.artwork.id],
            'share_type': 'artwork',
            'recipient_type': 'specific',
            'expiration_type': 'never',
            'recipient_user_ids': [recipient.id],
        }
        notification = Notification.objects.filter(
            user=recipient,
            content_code=NOTIFICATIONS_CONTENT_CODE.SHARE_LINK_INVITATION,
        ).count()
        self.assertEqual(notification, 0)

        response = self.client.post('/api/artwork/share_links/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        notification = Notification.objects.filter(
            user=recipient,
            content_code=NOTIFICATIONS_CONTENT_CODE.SHARE_LINK_INVITATION,
        ).count()
        self.assertEqual(notification, 1)

    def test_create_share_link_without_title_uses_correct_notification(self):
        recipient = UserFactory()
        data = {
            'artwork': [self.artwork.id],
            'share_type': 'artwork',
            'recipient_type': 'specific',
            'expiration_type': 'never',
            'recipient_user_ids': [recipient.id],
        }
        notification = Notification.objects.filter(
            user=recipient,
            content_code=NOTIFICATIONS_CONTENT_CODE.SHARE_LINK_INVITATION_NO_TITLE,
        ).count()
        self.assertEqual(notification, 0)

        response = self.client.post('/api/artwork/share_links/', data=data, format='json')

        notification = Notification.objects.filter(
            user=recipient,
            content_code=NOTIFICATIONS_CONTENT_CODE.SHARE_LINK_INVITATION_NO_TITLE,
        ).count()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(notification, 1)


class ShareLinkExtraCoverageTests(BaseUserTest):
    def test_share_link_viewset_get_serializer_class_default_falls_back_to_create(self):
        viewset = ShareLinkViewSet()
        viewset.action = 'create'

        serializer_class = viewset.get_serializer_class()

        from artwork.serializers.share_link import ShareLinkCreateSerializer
        self.assertIs(serializer_class, ShareLinkCreateSerializer)

    def test_share_link_viewset_perform_create_sets_user(self):
        factory = APIRequestFactory()
        request = factory.post('/api/artwork/share_links/', data={}, format='json')
        request.user = self.user

        viewset = ShareLinkViewSet()
        viewset.request = request

        class DummySerializer:
            def __init__(self):
                self.saved_kwargs = None

            def save(self, **kwargs):
                self.saved_kwargs = kwargs

        serializer = DummySerializer()
        viewset.perform_create(serializer)

        self.assertEqual(serializer.saved_kwargs, {'user': self.user})

    def test_create_share_link_single_type_auto_detect_sets_share_type(self):
        artwork = ArtworkFactory(owner=self.user, is_public=True)

        data = {
            'title': 'Auto Detect Single',
            'artwork': [artwork.id],
            'recipient_type': 'public',
            'expiration_type': 'never',
        }

        response = self.client.post('/api/artwork/share_links/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data.get('share_type'), 'artwork')

    def test_create_share_link_ignores_nonexistent_recipient_user_ids(self):
        artwork = ArtworkFactory(owner=self.user, is_public=True)

        data = {
            'title': 'Nonexistent Recipient',
            'artwork': [artwork.id],
            'recipient_type': 'specific',
            'expiration_type': 'never',
            'recipient_user_ids': [999999999],
        }

        response = self.client.post('/api/artwork/share_links/', data=data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        share_link = ShareLink.objects.get(id=response.data['id'])
        self.assertEqual(share_link.recipients.count(), 0)

    def test_validate_recipient_allows_authenticated_recipient_in_list(self):
        from artwork.utils.mixin.share_link import ShareLinkValidateMixin

        owner = UserFactory()
        recipient_user = UserFactory()

        share_link = ShareLinkFactory(
            user=owner,
            recipient_type='specific',
            is_active=True,
        )
        share_link.recipients.add(recipient_user)

        factory = APIRequestFactory()
        request = factory.get('/api/artwork/share/test/')
        request.user = recipient_user

        mixin = ShareLinkValidateMixin()
        mixin.validate_recipient(share_link, request)


class ShareLinkModelMethodsTest(BaseUserTest):

    def setUp(self) -> None:
        super().setUp()
        self.artwork = ArtworkFactory(owner=self.user, is_public=True)

    def test_get_shared_collections_returns_none_when_not_share_all(self):
        share_link = ShareLinkFactory(
            user=self.user,
            is_share_all=False,
        )
        share_link.artwork.add(self.artwork)

        result = share_link.get_shared_collections()

        self.assertEqual(result.count(), 0)

    def test_get_shared_exhibitions_returns_none_when_not_share_all(self):
        share_link = ShareLinkFactory(
            user=self.user,
            is_share_all=False,
        )
        share_link.artwork.add(self.artwork)

        result = share_link.get_shared_exhibitions()

        self.assertEqual(result.count(), 0)

    def test_get_shared_artworks_returns_all_when_share_all_true(self):
        artwork2 = ArtworkFactory(owner=self.user, is_public=True)
        artwork3 = ArtworkFactory(owner=self.user, is_public=False)

        share_link = ShareLinkFactory(
            user=self.user,
            is_share_all=True,
        )

        result = share_link.get_shared_artworks()

        self.assertEqual(result.count(), 3)
        self.assertIn(self.artwork, result)
        self.assertIn(artwork2, result)
        self.assertIn(artwork3, result)

    def test_get_shared_exhibitions_returns_all_when_share_all_true(self):
        exhibition1 = ExhibitionFactory(owner=self.user, is_public=True)
        exhibition2 = ExhibitionFactory(owner=self.user, is_public=False)

        share_link = ShareLinkFactory(
            user=self.user,
            is_share_all=True,
        )

        result = share_link.get_shared_exhibitions()

        self.assertEqual(result.count(), 2)
        self.assertIn(exhibition1, result)
        self.assertIn(exhibition2, result)

    def test_add_recipient_adds_user_to_recipients(self):
        share_link = ShareLinkFactory(
            user=self.user,
            recipient_type='specific',
        )
        share_link.artwork.add(self.artwork)
        new_recipient = UserFactory()

        self.assertEqual(share_link.recipients.count(), 0)

        share_link.add_recipient(new_recipient)

        self.assertEqual(share_link.recipients.count(), 1)
        self.assertTrue(share_link.recipients.filter(id=new_recipient.id).exists())

    def test_get_share_url_with_request(self):
        from django.test import RequestFactory

        share_link = ShareLinkFactory(
            user=self.user,
        )
        share_link.artwork.add(self.artwork)

        factory = RequestFactory()
        request = factory.get('/api/artwork/share/')

        url = share_link.get_share_url(request=request)

        self.assertIn(str(share_link.id), url)
        self.assertIn('/api/artwork/share/', url)
        self.assertIn('http', url)
        self.assertIn('testserver', url)

    def test_get_share_url_without_request(self):
        share_link = ShareLinkFactory(
            user=self.user,
        )
        share_link.artwork.add(self.artwork)

        url = share_link.get_share_url(request=None)

        self.assertEqual(url, f'/api/artwork/share/{share_link.id}/')

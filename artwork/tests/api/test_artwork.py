from django.conf import settings
from faker import Faker
from rest_framework import status
from artwork.factories.artwork_artist import ArtworkArtistFactory
from artwork.factories.collection import CollectionFactory
from artwork.factories.condition_image_batch import ConditionImageBatchFactory, ConditionImageFactory
from artwork.factories.style_artwork import StyleArtworkFactory
from artwork.models import (ImageArtwork, ImageCertificateRequest, ArtWork,
                            ArtworkArtist, ConditionImageBatch,
                            ConditionImage, ConditionImageBatchLog)
from artwork.models.style_artwork import StyleArtwork
from artwork.factories.artwork import ArtworkFactory
from artwork.factories.artwork_certificate import ArtworkCertificateFactory
from artwork.factories.image_artwork import ImageArtworkFactory
from artwork.factories.size_artwork import SizeArtworkFactory
from artwork.factories.artwork_edition import ArtworkEditionFactory
from artwork.factories.certificate_request import CertificateRequestFactory
from artwork.factories.medium_artwork import MediumArtworkFactory
from artwork.factories.share_link import ShareLinkFactory
from artwork.utils.const import CATEGORY_CHOICES
from artwork.tests.utils.artwork import create_data as utils_create_data

from core.accounts.factories.user import UserLocationFactory, UserFactory
from core.accounts.tests.api.base_user_test import BaseUserTest
from core.accounts.models.user import USER_ROLE
from artwork.factories.owner_certificate import OwnerCertificateFactory
from artwork.models.artwork_edition import ArtworkEdition
from artwork.models.certificate_request import CertificateRequest
from artwork.models.certificate_request import STATUS
from artwork.models.artwork_certificate import ArtworkCertificate
from django.utils import timezone
from datetime import timedelta
import jwt
from artwork.utils.artwork import get_artworks_by_role
import uuid

faker = Faker()


class ArtworkApiTest(BaseUserTest):
    def setUp(self) -> None:
        super().setUp()
        self.user.role = USER_ROLE.ARTIST
        self.user.save()
        self.user_location = UserLocationFactory(user=self.user)

    def assert_create_artwork(self, response, data):
        self.assertEqual(response.data['title'], data['title'])
        self.assertEqual(response.data['description'], data['description'])
        self.assertEqual(response.data['note'], data['note'])
        self.assertEqual(response.data['category'], data['category'])
        self.assertEqual(response.data['status'], data['status'])
        self.assertTrue(response.data['is_public'])
        self.assertFalse(response.data['is_hide_price'])
        self.assertEqual(response.data['currency'], data['currency'])
        self.assertEqual(response.data['year_created'], data['year_created'])
        self.assertEqual(response.data['total_edition'], data['total_edition'])

    def _create_data(self, **overrides):
        return utils_create_data(self.user.id, location=self.user_location.id, **overrides)

    def test_create_artwork(self):
        data = self._create_data(artist_id=self.user.id)
        size_data = data['size']

        response = self.client.post(
            '/api/artwork/artwork/',
            data=data,
            format='json',
        )

        image_artwork = ImageArtwork.objects.last()
        editions = ArtworkEdition.objects.count()
        edition_first = ArtworkEdition.objects.first()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        artwork = ArtWork.objects.first()
        self.assertEqual(artwork.artist, self.user)

        self.assert_create_artwork(response, data)
        self.assertEqual(response.data['style']['name'], data['style']['name'])
        self.assertEqual(response.data['subject']['name'], data['subject']['name'])
        self.assertEqual(response.data['medium']['name'], data['medium']['name'])

        self.assertEqual(response.data['location'], self.user_location.id)
        actual_price = str(response.data['price']).rstrip('0').rstrip('.')
        self.assertEqual(actual_price, '1000000')
        self.assertEqual(response.data['total_edition'], editions)
        self.assertEqual(edition_first.status, 'sold')
        self.assertEqual(edition_first.location.id, self.user_location.id)

        self.assertEqual(float(response.data['size']['length']), size_data['length'])
        self.assertEqual(image_artwork.image, 'image_2.png')

    def test_utils_get_artworks_by_role_returns_queryset_when_owner(self):
        owner = UserFactory()
        artwork = ArtworkFactory(owner=owner)

        qs = get_artworks_by_role(owner, is_owner=True)
        self.assertIsNotNone(qs)
        self.assertEqual(list(qs), [artwork])

    def test_utils_get_artworks_by_role_returns_none_when_not_owner(self):
        owner = UserFactory()

        qs = get_artworks_by_role(owner, is_owner=False)
        self.assertIsNone(qs)

    def test_get_detail_artwork_by_certificate_code(self):
        owner = OwnerCertificateFactory()
        certificate = owner.certificate
        artwork = certificate.artwork_edition.artwork
        edition = certificate.artwork_edition
        edition.edition_number = 1
        edition.save()

        response = self.client.get(f'/api/artwork/artwork/{certificate.code}/', format='json')

        view_url = f'{settings.PRIMARY_SITE_URL}/view-certificate/{certificate.code}'

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], artwork.id)
        self.assertEqual(response.data['artist_artwork']['artist_name'], artwork.artist_artwork.artist_name)
        self.assertEqual(response.data['certificate']['code'], str(certificate.code))
        self.assertEqual(response.data['certificate']['edition_number'], 1)
        self.assertEqual(response.data['certificate']['view_url'], view_url)

    def test_get_detail_artwork_not_found_when_uuid_not_exists(self):
        missing_uuid = uuid.uuid4()

        response = self.client.get(f'/api/artwork/artwork/{missing_uuid}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['detail'], 'Not found.')

    def test_collector_create_artwork_by_add_artist_manually(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()

        artist_artwork = {
            'artist_name': 'Johny',
            'contact_info': 'johny@gmail.com',
            'year_of_birth': '2000',
            'create_user': self.user.id,
        }
        data = self._create_data(artist_artwork=artist_artwork, edition_number=1)
        response = self.client.post(
            '/api/artwork/artwork/',
            data=data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        artwork = ArtWork.objects.first()
        self.assertEqual(artwork.artist_artwork.artist_name, 'Johny')
        self.assertEqual(artwork.artist_artwork.create_user, self.user)

    def test_collector_create_artwork_by_add_artist_on_platform(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()

        artist = UserFactory()
        data = self._create_data(artist_id=artist.id, edition_number=1)

        response = self.client.post(
            '/api/artwork/artwork/',
            data=data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        artwork = ArtWork.objects.first()
        self.assertEqual(artwork.artist.id, artist.id)

    def test_should_not_create_artwork_artist_if_already_exist_artwork_artist_data(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()

        artist = ArtworkArtistFactory(artist_name='Johny', create_user=self.user,
                                      year_of_birth='2021', contact_info='0909xxxyyy')

        artist_artwork = {
            'artist_name': artist.artist_name,
            'year_of_birth': artist.year_of_birth,
            'contact_info': artist.contact_info,
        }
        data = self._create_data(artist_artwork=artist_artwork, edition_number=1)
        response = self.client.post(
            '/api/artwork/artwork/',
            data=data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        artwork = ArtWork.objects.first()
        self.assertEqual(artwork.artist_artwork.artist_name, 'Johny')
        self.assertEqual(artwork.artist_artwork.create_user, self.user)
        self.assertEqual(ArtworkArtist.objects.count(), 1)

    def test_create_artwork_user_role_collector(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()

        data = self._create_data(edition_number=1)

        response = self.client.post(
            '/api/artwork/artwork/',
            data=data,
            format='json',
        )
        editions = ArtworkEdition.objects.all()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assert_create_artwork(response, data)
        self.assertEqual(response.data['location'], self.user_location.id)
        actual_price = str(response.data['price']).rstrip('0').rstrip('.')
        self.assertEqual(actual_price, '1000000')
        self.assertEqual(response.data['total_edition'], 1)
        self.assertEqual(len(editions), 1)
        self.assertEqual(editions[0].edition_number, 1)

    def test_should_raise_error_if_collector_create_artwork_and_not_has_edition_number(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()

        data = self._create_data()
        data.pop('style')

        response = self.client.post(
            '/api/artwork/artwork/',
            data=data,
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'edition_number': ['Edition number is required']})

    def test_should_raise_error_if_create_artwork_image_reach_limit(self):
        images = [
            'image_1.png',
            'image_2.png',
            'image_3.png',
            'image_4.png',
            'image_5.png',
            'image_6.png',
        ]
        data = self._create_data(images=images)
        response = self.client.post(
            '/api/artwork/artwork/',
            data=data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_should_raise_error_if_total_edition_greater_than_20(self):
        data = self._create_data(total_edition=21, category='painting')

        response = self.client.post(
            '/api/artwork/artwork/',
            data=data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'total_edition': ['For paintings, the maximum total edition is 1.']})

    def test_category_sculpture_should_raise_error_if_total_edition_greater_than_100(self):
        data = self._create_data(total_edition=101, category='sculpture')

        response = self.client.post(
            '/api/artwork/artwork/',
            data=data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(),
                         {'total_edition': ['For sculptures, the maximum total edition is 100.']})

    def test_create_artwork_with_empty_images_field(self):
        data = self._create_data(images=[])
        response = self.client.post(
            '/api/artwork/artwork/',
            data=data,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'images': ['The images list must contain at least one item.']})

    def test_get_list_artwork(self):
        artist = UserFactory()
        ArtworkFactory(owner=artist)
        ArtworkFactory(owner=self.user)

        response = self.client.get('/api/artwork/artwork/', {
            'user_uuid': self.user.uuid,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_get_list_artist_name_for_collector_missing_user_uuid_permission_denied(self):
        response = self.client.get(
            '/api/artwork/artwork/list_artist_name_for_collector/',
            {},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'You do not have permission to access this artist list.')

    def test_get_list_artist_name_for_collector_by_share_link_filters_manual_artists(self):
        owner = UserFactory(role=USER_ROLE.COLLECTOR)

        artist_in_share = ArtworkArtistFactory(create_user=owner)
        artist_not_in_share = ArtworkArtistFactory(create_user=owner)

        shared_artwork = ArtworkFactory(owner=owner, artist_artwork=artist_in_share)
        ArtworkFactory(owner=owner, artist_artwork=artist_not_in_share)

        share_link = ShareLinkFactory(
            user=owner,
            share_type='artwork',
            recipient_type='public',
        )

        share_link.artwork.add(shared_artwork)

        self.client.credentials()
        response = self.client.get(
            '/api/artwork/artwork/list_artist_name_for_collector/',
            {
                'share_link_id': share_link.id,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['artist_name'], artist_in_share.artist_name)

    def test_list_artwork_should_response_certificate(self):
        artwork = ArtworkFactory(owner=self.user, total_edition=3, is_public_certificate=True)

        edition_1 = ArtworkEditionFactory(artwork=artwork, edition_number=1, status='available')
        edition_2 = ArtworkEditionFactory(artwork=artwork, edition_number=2, status='available')
        ArtworkEditionFactory(artwork=artwork, edition_number=3)

        certificate_1 = ArtworkCertificateFactory(artwork_edition=edition_1)
        ArtworkCertificateFactory(artwork_edition=edition_2)

        response = self.client.get('/api/artwork/artwork/', {
            'user_uuid': self.user.uuid,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        artwork = response.data['results'][0]
        self.assertIsNotNone(artwork['certificate'])
        self.assertEqual(artwork['certificate']['code'], str(certificate_1.code))

    def test_list_artwork_should_response_certificate_status_false_if_not_match_status(self):
        artwork = ArtworkFactory(owner=self.user, total_edition=3)

        edition_1 = ArtworkEditionFactory(artwork=artwork, edition_number=1, status='sold')

        ArtworkCertificateFactory(artwork_edition=edition_1)

        response = self.client.get('/api/artwork/artwork/', {
            'user_uuid': self.user.uuid,
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

        artwork = response.data['results'][0]
        self.assertFalse(artwork['is_public_certificate'])

    def test_list_artwork_certificate_from_linked_artworks(self):
        artwork = ArtworkFactory(owner=self.user, total_edition=3, is_public_certificate=True)
        edition = ArtworkEditionFactory(artwork=artwork)

        artwork_2 = ArtworkFactory(linked_artwork=artwork)
        ArtworkEditionFactory(artwork=artwork_2, linked_edition=edition)
        certificate = ArtworkCertificateFactory(artwork_edition=edition, issued_by=self.user)

        response = self.client.get('/api/artwork/artwork/', {
            'user_uuid': self.user.uuid,
        }, format='json')

        artwork_response = response.data['results'][0]
        self.assertEqual(artwork_response['id'], artwork.id)
        self.assertIsNotNone(artwork_response['certificate'])
        self.assertEqual(artwork_response['certificate']['id'], certificate.id)

    def test_list_artwork_certificate_from_linked_artwork(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()

        artwork = ArtworkFactory()
        edition = ArtworkEditionFactory(artwork=artwork)
        certificate = ArtworkCertificateFactory(artwork_edition=edition, issued_to=self.user)

        artwork_2 = ArtworkFactory(linked_artwork=artwork, owner=self.user, is_public_certificate=True)
        ArtworkEditionFactory(artwork=artwork_2, linked_edition=edition)

        response = self.client.get('/api/artwork/artwork/', {
            'user_uuid': self.user.uuid,
        }, format='json')

        artwork_response = response.data['results'][0]
        self.assertEqual(artwork_response['id'], artwork_2.id)
        self.assertIsNotNone(artwork_response['certificate'])
        self.assertEqual(artwork_response['certificate']['id'], certificate.id)

    def test_get_detail_artwork(self):
        size = SizeArtworkFactory(width=1, height=2.5, depth=3.0)
        artwork = ArtworkFactory(artist=self.user, status='available', size=size)
        ImageArtworkFactory(artwork=artwork)
        ImageArtworkFactory(artwork=artwork)

        response = self.client.get(f'/api/artwork/artwork/{artwork.uuid}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], artwork.id)
        self.assertEqual(response.data['artist_artwork']['artist_name'], artwork.artist_artwork.artist_name)
        self.assertEqual(response.data['size']['width'], 1)
        self.assertEqual(response.data['size']['height'], 2.5)
        self.assertEqual(response.data['size']['depth'], 3)
        self.assertEqual(response.data['status'], {'key': 'available', 'value': 'Available for sale'})
        self.assertIsNone(response.data['certificate'])

    def test_get_detail_artwork_field_edition(self):
        artwork = ArtworkFactory(artist=self.user, status='available')
        edition = ArtworkEditionFactory(artwork=artwork)
        certificate = ArtworkCertificateFactory(artwork_edition=edition)
        response = self.client.get(f'/api/artwork/artwork/{artwork.uuid}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], artwork.id)
        editions = response.data['editions']
        self.assertEqual(editions[0]['id_certificate'], certificate.code)

    def test_get_detail_artwork_field_edition_by_linked_edition(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)
        artwork_2 = ArtworkFactory(owner=artist)
        edition_2 = ArtworkEditionFactory(artwork=artwork_2)
        certificate = ArtworkCertificateFactory(artwork_edition=edition_2)

        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        artwork = ArtworkFactory(owner=self.user, status='available', linked_artwork=artwork_2)
        ArtworkEditionFactory(artwork=artwork, linked_edition=edition_2)

        response = self.client.get(f'/api/artwork/artwork/{artwork.uuid}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], artwork.id)
        editions = response.data['editions']
        self.assertEqual(editions[0]['id_certificate'], certificate.code)

    def test_get_detail_artwork_field_edition_by_linked_edition_related(self):
        artwork = ArtworkFactory(owner=self.user, status='available')
        edition = ArtworkEditionFactory(artwork=artwork)

        collector = UserFactory(role=USER_ROLE.COLLECTOR)
        artwork_2 = ArtworkFactory(owner=collector, linked_artwork=artwork)
        edition_2 = ArtworkEditionFactory(artwork=artwork_2, linked_edition=edition)
        certificate = ArtworkCertificateFactory(artwork_edition=edition_2)

        response = self.client.get(f'/api/artwork/artwork/{artwork.uuid}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], artwork.id)
        editions = response.data['editions']
        self.assertEqual(editions[0]['id_certificate'], certificate.code)

    def test_get_detail_artwork_case_not_permission(self):
        artwork = ArtworkFactory(is_public=False)
        ImageArtworkFactory(artwork=artwork)
        ImageArtworkFactory(artwork=artwork)

        response = self.client.get(f'/api/artwork/artwork/{artwork.uuid}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'You do not have permission to access this artwork.')

    def test_artwork_attribute_certificate_should_be_true_if_linked_already_has_certificate(self):
        linked_artwork = ArtworkFactory(artist=self.user, status='available')
        ArtworkCertificateFactory(artwork_edition__artwork=linked_artwork)
        artwork = ArtworkFactory(artist=self.user, status='available', linked_artwork=linked_artwork)

        response = self.client.get(f'/api/artwork/artwork/{artwork.uuid}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['has_certificate'])

    def test_get_detail_artwork_but_wrong_certificate_code(self):
        OwnerCertificateFactory()

        response = self.client.get('/api/artwork/artwork/xxxxxxx/', format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_update_artwork_artist_in_platform(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        artist = UserFactory(role=USER_ROLE.ARTIST)
        artwork = ArtworkFactory(owner=self.user, status='available')

        data = self._create_data(artist_id=artist.id)
        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            data=data,
            format='json',
        )
        artwork.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(artwork.artist.id, artist.id)

    def test_update_artwork(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        artwork = ArtworkFactory(owner=self.user, status='available')
        artist_artwork = {
            'artist_name': 'John',
            'contact_info': '',
            'year_of_birth': '2021',
        }
        data = self._create_data(artist_artwork=artist_artwork)
        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            data=data,
            format='json',
        )
        artwork.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(artwork.title, data['title'])
        self.assertEqual(artwork.artist_artwork.artist_name, data['artist_artwork']['artist_name'])
        self.assertEqual(artwork.artist_artwork.create_user, self.user)
        self.assertEqual(ArtworkArtist.objects.count(), 2)

    def test_update_artwork_should_not_create_new_artist_if_user_select_exist_artist(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        artist = ArtworkArtistFactory(create_user=self.user)
        artwork = ArtworkFactory(owner=self.user, status='available')
        artist_artwork = {
            'artist_name': artist.artist_name,
            'year_of_birth': artist.year_of_birth,
        }
        data = self._create_data(artist_artwork=artist_artwork)
        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            data=data,
            format='json',
        )
        artwork.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(artwork.title, data['title'])
        self.assertEqual(artwork.artist_artwork.artist_name, data['artist_artwork']['artist_name'])
        self.assertEqual(artwork.artist_artwork.create_user, self.user)
        self.assertEqual(ArtworkArtist.objects.count(), 2)

    def test_collector_update_artwork_edition(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        artwork = ArtworkFactory(owner=self.user, status='available', total_edition=10)
        edition = ArtworkEditionFactory(artwork=artwork, edition_number=3)

        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            data={
                'edition': {
                    'id': edition.id,
                    'edition_number': 5,
                },
            },
            format='json',
        )
        edition.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(edition.edition_number, 5)

    def test_should_create_edition_if_collector_update_artwork_but_edition_not_exist(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        artwork = ArtworkFactory(owner=self.user, status='available', total_edition=10)

        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            data={
                'edition': {
                    'edition_number': 5,
                },
            },
            format='json',
        )

        editions = ArtworkEdition.objects.all()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(editions), 1)
        self.assertEqual(editions[0].artwork, artwork)
        self.assertEqual(editions[0].edition_number, 5)

    def test_not_allow_update_artwork_if_user_is_not_owner(self):
        user = UserFactory()
        artwork = ArtworkFactory(artist=user, status='available')
        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            {
                'title': '123',
                'description': 'description',
                'category': 'painting',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'You do not have permission to edit this artwork.')

    def test_update_condition_images_create_batch_and_images(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        artwork = ArtworkFactory(owner=self.user, status='available')
        artwork_edition = ArtworkEditionFactory(artwork=artwork)
        ArtworkCertificateFactory(artwork_edition=artwork_edition)
        payload = {
            'title': 't1',
            'description': 'd1',
            'category': 'painting',
            'condition_images': ['c1.png', 'c2.png', 'c3.png'],
        }
        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            payload,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        batch = ConditionImageBatch.objects.get(artwork=artwork, owner=self.user)
        self.assertEqual(batch.update_count, 1)

        imgs = list(ConditionImage.objects.filter(batch=batch).order_by('order', 'id'))
        self.assertEqual([str(i.image) for i in imgs], payload['condition_images'])
        self.assertEqual([i.order for i in imgs], [0, 1, 2])

        logs = ConditionImageBatchLog.objects.filter(batch=batch)
        self.assertEqual(logs.count(), 1)
        self.assertEqual(logs.first().images_snapshot, payload['condition_images'])

    def test_update_condition_images_no_new_images_to_add(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        artwork = ArtworkFactory(owner=self.user, status='available')
        artwork_edition = ArtworkEditionFactory(artwork=artwork)
        ArtworkCertificateFactory(artwork_edition=artwork_edition)

        batch = ConditionImageBatchFactory(artwork=artwork, owner=self.user)
        ConditionImageFactory(batch=batch, image='img1.png', order=0)
        ConditionImageFactory(batch=batch, image='img2.png', order=1)

        initial_count = ConditionImage.objects.filter(batch=batch).count()
        self.assertEqual(initial_count, 2)

        updated_images = ['img2.png']

        payload = {
            'title': 't1',
            'description': 'd1',
            'category': 'painting',
            'condition_images': updated_images,
        }

        initial_condition_images = list(ConditionImage.objects.filter(batch=batch).values_list('id', flat=True))

        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            payload,
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        final_condition_images = list(ConditionImage.objects.filter(batch=batch).values_list('id', flat=True))
        self.assertEqual(set(final_condition_images).issubset(initial_condition_images), True)

        batch.refresh_from_db()

        final_images = list(
            ConditionImage.objects
                          .filter(batch=batch)
                          .order_by('order')
                          .values_list('image', flat=True),
        )

        self.assertEqual(final_images, updated_images)
        self.assertEqual(len(final_images), 1)
        self.assertEqual(final_images[0], 'img2.png')

        self.assertEqual(batch.update_count, 1)

    def test_update_condition_images_add_and_remove_images(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        artwork = ArtworkFactory(owner=self.user, status='available')
        artwork_edition = ArtworkEditionFactory(artwork=artwork)
        ArtworkCertificateFactory(artwork_edition=artwork_edition)

        initial_images = ['img1.png', 'img2.png', 'img3.png']
        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            {'title': 't1', 'condition_images': initial_images},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        batch = ConditionImageBatch.objects.get(artwork=artwork, owner=self.user)
        initial_count = ConditionImage.objects.filter(batch=batch).count()
        self.assertEqual(initial_count, 3)

        updated_images = ['img3.png', 'img1.png', 'img4.png']
        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            {'title': 't1', 'condition_images': updated_images},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        batch.refresh_from_db()
        self.assertEqual(batch.update_count, 2)

        final_images = list(
            ConditionImage.objects
                          .filter(batch=batch)
                          .order_by('order')
                          .values_list('image', flat=True),
        )
        self.assertEqual(final_images, updated_images)

        self.assertEqual(len(final_images), 3)
        self.assertIn('img4.png', final_images)
        self.assertNotIn('img2.png', final_images)
        self.assertEqual(final_images.index('img3.png'), 0)  # Verify order
        self.assertEqual(final_images.index('img1.png'), 1)

        # Verify log was created
        logs = ConditionImageBatchLog.objects.filter(batch=batch)
        self.assertEqual(logs.count(), 2)
        self.assertEqual(logs.last().images_snapshot, updated_images)

    def test_update_condition_images_no_changes_does_not_increment_or_log(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        artwork = ArtworkFactory(owner=self.user, status='available')
        artwork_edition = ArtworkEditionFactory(artwork=artwork)
        ArtworkCertificateFactory(artwork_edition=artwork_edition)

        first = ['a.png', 'b.png']

        r1 = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            {'title': 'x', 'description': 'y', 'category': 'painting', 'condition_images': first},
            format='json',
        )
        self.assertEqual(r1.status_code, status.HTTP_200_OK)
        batch = ConditionImageBatch.objects.get(artwork=artwork, owner=self.user)
        self.assertEqual(batch.update_count, 1)

        r2 = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            {'title': 'x2', 'description': 'y2', 'category': 'painting', 'condition_images': first},
            format='json',
        )
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        batch.refresh_from_db()
        self.assertEqual(batch.update_count, 1)
        self.assertEqual(ConditionImageBatchLog.objects.filter(batch=batch).count(), 1)

    def test_update_condition_images_two_updates_allowed_then_reject_third(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        artwork = ArtworkFactory(owner=self.user, status='available')
        artwork_edition = ArtworkEditionFactory(artwork=artwork)
        ArtworkCertificateFactory(artwork_edition=artwork_edition)

        lists = [
            ['i1.png', 'i2.png', 'i3.png'],
            ['i2.png', 'i3.png', 'i4.png'],
            ['i3.png', 'i4.png'],
        ]

        r1 = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            {'title': 't', 'description': 'd', 'category': 'painting', 'condition_images': lists[0]},
            format='json',
        )
        self.assertEqual(r1.status_code, status.HTTP_200_OK)
        batch = ConditionImageBatch.objects.get(artwork=artwork, owner=self.user)
        self.assertEqual(batch.update_count, 1)

        r2 = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            {'title': 't2', 'description': 'd2', 'category': 'painting', 'condition_images': lists[1]},
            format='json',
        )
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        batch.refresh_from_db()
        self.assertEqual(batch.update_count, 2)

        imgs = list(ConditionImage.objects.filter(batch=batch).order_by('order', 'id'))
        self.assertEqual([str(i.image) for i in imgs], lists[1])
        self.assertEqual([i.order for i in imgs], [0, 1, 2])

        r3 = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            {'title': 't3', 'description': 'd3', 'category': 'painting', 'condition_images': lists[2]},
            format='json',
        )
        self.assertEqual(r3.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('condition_images', r3.data)
        self.assertIn('update condition images up to 2 times', str(r3.data))

    def test_update_images_artwork(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        title = faker.sentence()
        description = faker.paragraph()
        style = StyleArtworkFactory(category='painting', name='style1')
        artwork = ArtworkFactory(owner=self.user, status='available', style=style)
        ImageArtworkFactory(artwork=artwork)
        ImageArtworkFactory(artwork=artwork)
        ImageArtworkFactory(artwork=artwork, image='image_1.png')
        images = [
            'image_1.png',
            'image_2.png',
            'image_3.png',
        ]

        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/', {
                'title': title,
                'description': description,
                'category': 'painting',
                'images': images,
            },
        )
        image_artwork = ImageArtwork.objects.filter(artwork=artwork)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], title)
        self.assertEqual(response.data['description'], description)
        self.assertEqual(response.data['category'], 'painting')
        self.assertEqual(len(image_artwork), 3)
        self.assertEqual(image_artwork[0].image, images[0])
        self.assertEqual(image_artwork[1].image, images[1])

    def test_update_artwork_with_empty_images_field(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        artwork = ArtworkFactory(artist=self.user, status='available')
        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            {
                'title': 'title',
                'description': 'description',
                'category': 'painting',
                'images': [],
            },
            format='json',
        )
        self.assertResponseStatus(response, status.HTTP_400_BAD_REQUEST)

    def test_list_artwork_same_collection_for_collector(self):
        collector = UserFactory(role=USER_ROLE.COLLECTOR)
        artist = UserFactory(role=USER_ROLE.ARTIST)

        artwork1 = ArtworkFactory(owner=collector, artist=artist, year_created=2022, is_public=True)
        ArtworkFactory(owner=collector, artist=artist, year_created=2023, is_public=True)
        ArtworkFactory(owner=collector, artist=artist, year_created=2024, is_public=True)
        ArtworkFactory(owner=collector, is_public=True)  # Different artist

        url = '/api/artwork/artwork/list_artwork_same_collection/'
        params = {
            'owner_id': collector.id,
            'user_id': artist.id,
            'year_created': 2022,
            'artwork_id': artwork1.id,
        }

        response = self.client.get(url, data=params, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], artwork1.id)

    def test_list_artwork_same_collection_for_collector_no_filter_year(self):
        collector = UserFactory(role=USER_ROLE.COLLECTOR)
        artist = UserFactory(role=USER_ROLE.ARTIST)

        artwork1 = ArtworkFactory(owner=collector, artist=artist, year_created=2022, is_public=True)
        ArtworkFactory(owner=collector, artist=artist, year_created=2023, is_public=True)
        ArtworkFactory(owner=collector, artist=artist, year_created=2024, is_public=True)
        ArtworkFactory(owner=collector, is_public=True)

        url = '/api/artwork/artwork/list_artwork_same_collection/'
        params = {
            'owner_id': collector.id,
            'user_id': artist.id,
            'artwork_id': artwork1.id,
        }

        response = self.client.get(url, data=params, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)

    def test_update_artwork_set_artist_artwork_to_none(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        artwork_artist = ArtworkArtistFactory(create_user=self.user)
        artwork = ArtworkFactory(owner=self.user, artist_artwork=artwork_artist)

        self.assertIsNotNone(artwork.artist_artwork)

        data = {
            'artist_artwork': None,
        }

        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            data=data,
            format='json',
        )

        artwork.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNone(artwork.artist_artwork)

    def test_update_artwork_with_images_field_reach_limit(self):
        images = [
            'image_1.png',
            'image_2.png',
            'image_3.png',
            'image_4.png',
            'image_5.png',
            'image_6.png',
        ]
        artwork = ArtworkFactory(artist=self.user, status='available')
        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            {
                'title': 'title',
                'description': 'description',
                'category': 'painting',
                'images': images,
            },
            format='json',
        )
        self.assertResponseStatus(response, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['non_field_errors'], ['The images list must not contain more than five items.'])

    def test_should_not_update_none_allow_field_with_artwork_has_certificate(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        artwork = ArtworkFactory(owner=self.user, status='available')
        artwork_edition = ArtworkEditionFactory(artwork=artwork)
        ArtworkCertificateFactory(artwork_edition=artwork_edition)

        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            {
                'title': 'Updated Title',
                'total_edition': 10,
            },
            format='json',
        )

        artwork.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(artwork.title, 'Updated Title')
        self.assertNotEqual(artwork.total_edition, 10)

    def test_should_update_allow_field_with_artwork_has_certificate(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        artwork = ArtworkFactory(owner=self.user, artist=self.user, status='available')
        artwork_edition = ArtworkEditionFactory(artwork=artwork)
        ArtworkCertificateFactory(artwork_edition=artwork_edition)

        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            {
                'is_public': True,
                'is_public_certificate': True,
                'description': 'This is description',
                'note': 'This is note',
            },
            format='json',
        )
        artwork.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(artwork.is_public)
        self.assertTrue(artwork.is_public_certificate)
        self.assertEqual(artwork.description, response.data['description'])
        self.assertEqual(artwork.note, response.data['note'])

    def test_update_less_fields_propagates_description_to_linked_artworks_when_artist(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        artwork = ArtworkFactory(owner=self.user, artist=self.user, status='available')
        edition = ArtworkEditionFactory(artwork=artwork)
        ArtworkCertificateFactory(artwork_edition=edition)

        linked_1 = ArtworkFactory(linked_artwork=artwork, description='old 1')
        linked_2 = ArtworkFactory(linked_artwork=artwork, description='old 2')

        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            {
                'description': 'new description',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        linked_1.refresh_from_db()
        linked_2.refresh_from_db()
        artwork.refresh_from_db()

        self.assertEqual(artwork.description, 'new description')
        self.assertEqual(linked_1.description, 'old 1')
        self.assertEqual(linked_2.description, 'old 2')

    def test_update_less_fields_does_not_propagate_description_when_not_artist(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()

        artwork = ArtworkFactory(owner=self.user, status='available')
        edition = ArtworkEditionFactory(artwork=artwork)
        ArtworkCertificateFactory(artwork_edition=edition)

        linked = ArtworkFactory(linked_artwork=artwork, description='keep me')

        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            {
                'description': 'collector update',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        linked.refresh_from_db()
        artwork.refresh_from_db()

        self.assertEqual(artwork.description, 'collector update')
        self.assertEqual(linked.description, 'keep me')

    def test_update_less_fields_no_description_no_propagation(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        artwork = ArtworkFactory(owner=self.user, artist=self.user, status='available')
        edition = ArtworkEditionFactory(artwork=artwork)
        ArtworkCertificateFactory(artwork_edition=edition)

        linked = ArtworkFactory(linked_artwork=artwork, description='initial')

        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            {
                'note': 'only note change',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        linked.refresh_from_db()
        artwork.refresh_from_db()

        self.assertEqual(artwork.note, 'only note change')
        self.assertEqual(linked.description, 'initial')

    def test_update_size_artwork(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        title = faker.sentence()
        description = faker.paragraph()
        artwork = ArtworkFactory(owner=self.user, status='available')
        size_data = {
            'length': faker.random_int(min=1, max=1000) / 10.0,
            'width': faker.random_int(min=1, max=1000) / 10.0,
            'depth': faker.random_int(min=1, max=1000) / 10.0,
            'weight': faker.random_int(min=1, max=10000) / 10.0,
        }

        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            {
                'title': title,
                'description': description,
                'category': 'painting',
                'size': size_data,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], title)
        self.assertEqual(response.data['description'], description)
        self.assertEqual(response.data['category'], 'painting')
        self.assertEqual(float(response.data['size']['length']), size_data['length'])

    def test_update_artwork_size_when_existing(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        size_instance = SizeArtworkFactory()
        artwork = ArtworkFactory(owner=self.user, status='available', size=size_instance)
        new_size_data = {
            'length': 25.0,
            'width': 15.0,
            'depth': 10.0,
            'weight': 5.0,
        }

        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            {
                'size': new_size_data,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['size']['length']), new_size_data['length'])

    def test_update_artwork_size(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        artwork = ArtworkFactory(owner=self.user, status='available', size=None)
        new_size_data = {
            'length': 25.0,
            'width': 15.0,
            'depth': 10.0,
            'weight': 5.0,
        }

        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            {
                'size': new_size_data,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['size']['length']), new_size_data['length'])

    def test_update_artwork_in_stock_propagates_status_to_editions(self):
        artwork = ArtworkFactory(owner=self.user, status='in_stock')
        edition_1 = ArtworkEditionFactory(artwork=artwork, status='sold')
        edition_2 = ArtworkEditionFactory(artwork=artwork, status='available')

        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/update_artwork_in_stock/',
            {
                'status': 'available',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'available')

        edition_1.refresh_from_db()
        edition_2.refresh_from_db()
        self.assertEqual(edition_1.status, 'available')
        self.assertEqual(edition_2.status, 'available')

    def test_update_artwork_in_stock_propagates_status_to_editions_not_status(self):
        artwork = ArtworkFactory(owner=self.user, status='in_stock')
        edition_1 = ArtworkEditionFactory(artwork=artwork, status='sold')
        edition_2 = ArtworkEditionFactory(artwork=artwork, status='available')

        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/update_artwork_in_stock/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'in_stock')

        edition_1.refresh_from_db()
        edition_2.refresh_from_db()
        self.assertEqual(edition_1.status, 'sold')
        self.assertEqual(edition_2.status, 'available')

    def test_artist_request_certificate(self):
        artwork = ArtworkFactory(artist=self.user, status='available', size=None, total_edition=3)
        artwork_edition_1 = ArtworkEditionFactory(artwork=artwork, status='available')
        ArtworkEditionFactory(artwork__artist=self.user)
        new_user = UserFactory()
        issued_to_id = new_user.id

        response = self.client.post(
            f'/api/artwork/artwork/{artwork.id}/create_certificate/',
            {
                'edition_id': artwork_edition_1.id,
                'issued_to_id': issued_to_id,
                'owner_info': {
                    'name': 'John',
                    'year_of_birth': '2021',
                    'address': 'abc address',
                    'contract_number': '112233',
                },
                'shipping_info': {
                    'recipient': 'John',
                    'address': 'test address',
                    'phone_number': '0909xxx',
                },
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        certificate = ArtworkCertificate.objects.first()
        artwork_edition_1.refresh_from_db()

        self.assertEqual(certificate.issued_by, self.user)
        self.assertEqual(certificate.issued_to, new_user)
        self.assertEqual(artwork_edition_1.status, 'sold')

    def test_request_certificate_should_not_copy_new_artwork_when_issue_to_request_user(self):
        artwork = ArtworkFactory(artist=self.user, status='available', size=None, total_edition=3)
        artwork_edition_1 = ArtworkEditionFactory(artwork=artwork, status='available')

        self.assertEqual(ArtWork.objects.count(), 1)

        response = self.client.post(
            f'/api/artwork/artwork/{artwork.id}/create_certificate/',
            {
                'edition_id': artwork_edition_1.id,
                'issued_to_id': self.user.id,
                'owner_info': {
                    'name': 'John',
                    'year_of_birth': '2021',
                    'address': 'abc address',
                    'contract_number': '112233',
                },
                'shipping_info': {
                    'recipient': 'John',
                    'address': 'test address',
                    'phone_number': '0909xxx',
                },
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ArtWork.objects.count(), 1)

    def test_should_not_allow_request_certificate_if_edition_exist_certificate(self):
        artwork = ArtworkFactory(artist=self.user, status='available', size=None, total_edition=3)
        artwork_edition = ArtworkEditionFactory(artwork=artwork)
        ArtworkCertificateFactory(artwork_edition=artwork_edition)
        new_user = UserFactory()
        issued_to_id = new_user.id

        response = self.client.post(
            f'/api/artwork/artwork/{artwork.id}/create_certificate/',
            {
                'edition_id': artwork_edition.id,
                'issued_to_id': issued_to_id,
                'owner_info': {
                    'name': 'John',
                    'year_of_birth': '2021',
                    'address': 'abc address',
                    'contract_number': '112233',
                },
                'shipping_info': {
                    'recipient': 'John',
                    'address': 'test address',
                    'phone_number': '0909xxx',
                },
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'edition_id': ['This artwork edition already has a certificate.']})

    def test_should_create_new_artwork_for_collector_when_artist_create_certificate(self):
        artwork = ArtworkFactory(artist=self.user, status='available', size=None, total_edition=3)
        artwork_edition_1 = ArtworkEditionFactory(artwork=artwork, status='available')
        ArtworkEditionFactory(artwork__artist=self.user)
        new_user = UserFactory()

        self.assertEqual(new_user.artworks_owner.count(), 0)

        response = self.client.post(
            f'/api/artwork/artwork/{artwork.id}/create_certificate/',
            {
                'edition_id': artwork_edition_1.id,
                'issued_to_id': new_user.id,
                'owner_info': {
                    'name': 'John',
                    'year_of_birth': '2021',
                    'address': 'abc address',
                    'contract_number': '112233',
                },
                'shipping_info': {
                    'recipient': 'John',
                    'address': 'test address',
                    'phone_number': '0909xxx',
                },
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(new_user.artworks_owner.count(), 1)

    def test_get_editions_can_request_certificate(self):
        artwork = ArtworkFactory()
        edition_1 = ArtworkEditionFactory(artwork=artwork)
        edition_2 = ArtworkEditionFactory(artwork=artwork)
        ArtworkCertificateFactory(artwork_edition=edition_1)

        response = self.client.get(
            f'/api/artwork/artwork/{artwork.uuid}/editions_can_request_certificate/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], edition_2.id)

    def test_get_editions_can_request_certificate_when_already_link_with_another_artwork(self):
        artwork = ArtworkFactory(owner=self.user)

        edition_1 = ArtworkEditionFactory(artwork=artwork, edition_number=1)
        edition_2 = ArtworkEditionFactory(artwork=artwork, edition_number=2)
        edition_3 = ArtworkEditionFactory(artwork=artwork, edition_number=3)
        ArtworkCertificateFactory(artwork_edition=edition_1)

        artwork_2 = ArtworkFactory(linked_artwork=artwork)
        edition_artwork_2 = ArtworkEditionFactory(artwork=artwork_2, edition_number=2, linked_edition=edition_2)
        ArtworkCertificateFactory(artwork_edition=edition_artwork_2)

        response = self.client.get(
            f'/api/artwork/artwork/{artwork.uuid}/editions_can_request_certificate/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], edition_3.id)

    def test_collector_request_certificate(self):
        from artwork.factories.image_artwork import ImageArtworkFactory
        artist = UserFactory(role=USER_ROLE.ARTIST)
        medium = MediumArtworkFactory(category='painting', user=UserFactory())
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        artwork = ArtworkFactory(owner=self.user, status='available', size=None, total_edition=3, title='Artwork 1')
        ImageArtworkFactory(artwork=artwork)
        ImageArtworkFactory(artwork=artwork)

        edition = ArtworkEditionFactory(artwork=artwork, edition_number=1, status='available')
        images = [
            'image_1.png',
            'image_2.png',
        ]

        response = self.client.post(
            f'/api/artwork/artwork/{artwork.uuid}/request_certificate/',
            {
                'artwork': {
                    'uuid': str(artwork.uuid),
                    'id': artwork.id,
                    'title': 'Mountain',
                    'size': {
                        'height': 1,
                        'width': 1,
                        'depth': 1,
                    },
                    'year_created': 2021,
                    'edition_number': 1,
                    'total_edition': 10,
                    'medium': {
                        'id': medium.id,
                        'name': medium.name,
                        'name_vi': medium.name_vi,
                        'category': medium.category,
                        'user': medium.user.id,
                    },
                },
                'edition': {
                    'id': edition.id,
                    'edition_number': 2,
                    'status': edition.status,
                    'location': edition.location.id,
                    'linked_edition': None,
                },
                'owner_info': {
                    'name': 'John',
                    'year_of_birth': '2021',
                    'address': 'abc address',
                    'contract_number': '112233',
                },
                'shipping_info': {
                    'recipient': 'John',
                    'address': 'test address',
                    'phone_number': '0909xxx',
                },
                'request_to': artist.id,
                'images': images,
            },
            format='json',
        )

        certificate_request = CertificateRequest.objects.first()
        image_certificate_request = ImageCertificateRequest.objects.last()

        artwork.refresh_from_db()
        edition.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(artwork.title, 'Mountain')
        self.assertEqual(artwork.year_created, 2021)
        self.assertEqual(artwork.total_edition, 10)

        self.assertEqual(edition.edition_number, 2)

        self.assertEqual(certificate_request.request_by, self.user)
        self.assertEqual(certificate_request.request_to, artist)
        self.assertEqual(certificate_request.status, STATUS.REQUEST_RECEIVED)
        self.assertEqual(certificate_request.artwork_edition, edition)
        self.assertEqual(certificate_request.artwork_edition.artwork, artwork)
        self.assertEqual(certificate_request.artwork_edition.artwork.medium, medium)
        self.assertEqual(certificate_request.artwork_edition.edition_number, 2)

        self.assertEqual(image_certificate_request.image, 'image_2.png')

    def test_should_raise_error_if_artwork_not_has_any_edition(self):
        medium = MediumArtworkFactory(category='painting', user=UserFactory())
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        artist = UserFactory(role=USER_ROLE.ARTIST)
        artwork = ArtworkFactory(owner=self.user, status='available', size=None, total_edition=3, title='Artwork 1')
        edition = ArtworkEditionFactory(edition_number=1, status='available')
        images = [
            'image_1.png',
            'image_2.png',
        ]

        response = self.client.post(
            f'/api/artwork/artwork/{artwork.id}/request_certificate/',
            {
                'artwork': {
                    'uuid': str(artwork.uuid),
                    'id': artwork.id,
                    'title': 'Mountain',
                    'size': {
                        'height': 1,
                        'width': 1,
                        'depth': 1,
                    },
                    'year_created': 2021,
                    'edition_number': 1,
                    'total_edition': 10,
                    'medium': {
                        'id': medium.id,
                        'name': medium.name,
                        'name_vi': medium.name_vi,
                        'category': medium.category,
                        'user': medium.user.id,
                    },
                },
                'edition': {
                    'id': edition.id,
                    'edition_number': 2,
                    'status': edition.status,
                    'location': edition.location.id,
                },
                'owner_info': {
                    'name': 'John',
                    'year_of_birth': '2021',
                    'address': 'abc address',
                    'contract_number': '112233',
                },
                'shipping_info': {
                    'recipient': 'John',
                    'address': 'test address',
                    'phone_number': '0909xxx',
                },
                'request_to': artist.id,
                'images': images,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['artwork'][0],
                         'Artwork should have at least one edition to request certificate')

    def test_should_not_allow_request_certificate_if_already_has_request_certificate(self):
        medium = MediumArtworkFactory(category='painting')
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()

        artist = UserFactory(role=USER_ROLE.ARTIST)

        certificate_request = CertificateRequestFactory(request_by=self.user)
        edition = certificate_request.artwork_edition
        artwork = edition.artwork
        artwork.owner = self.user
        artwork.save()
        images = [
            'image_1.png',
            'image_2.png',
        ]
        response = self.client.post(
            f'/api/artwork/artwork/{artwork.id}/request_certificate/',
            {
                'artwork': {
                    'uuid': str(artwork.uuid),
                    'id': artwork.id,
                    'title': 'Mountain',
                    'size': {
                        'height': 1,
                        'width': 1,
                        'depth': 1,
                    },
                    'year_created': 2021,
                    'edition_number': 1,
                    'total_edition': 10,
                    'medium': {
                        'id': medium.id,
                        'name': medium.name,
                        'category': medium.category,
                    },
                },
                'edition': {
                    'id': edition.id,
                    'edition_number': edition.edition_number,
                    'linked_edition': None,
                },
                'owner_info': {
                    'name': 'John',
                    'year_of_birth': '2021',
                    'address': 'abc address',
                    'contract_number': '112233',
                },
                'shipping_info': {
                    'recipient': 'John',
                    'address': 'test address',
                    'phone_number': '0909xxx',
                },
                'request_to': artist.id,
                'images': images,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'artwork': ['This artwork already requested a certificate']})

    def test_collector_request_certificate_maximum_5_images(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)
        medium = MediumArtworkFactory(category='painting')
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        artwork = ArtworkFactory(owner=self.user, status='available', size=None, total_edition=3, title='Artwork 1')
        edition = ArtworkEditionFactory(artwork=artwork)
        images = [
            'image_1.png',
            'image_2.png',
            'image_3.png',
            'image_4.png',
            'image_5.png',
            'image_6.png',
        ]
        response = self.client.post(
            f'/api/artwork/artwork/{artwork.id}/request_certificate/',
            {
                'artwork': {
                    'uuid': str(artwork.uuid),
                    'id': artwork.id,
                    'title': 'Mountain',
                    'size': {
                        'height': 1,
                        'width': 1,
                        'depth': 1,
                    },
                    'year_created': 2021,
                    'edition_number': 1,
                    'total_edition': 10,
                    'medium': {
                        'id': medium.id,
                        'name': medium.name,
                        'category': medium.category,
                    },
                },
                'edition': {
                    'id': edition.id,
                    'edition_number': edition.edition_number,
                    'linked_edition': None,
                },
                'owner_info': {
                    'name': 'John',
                    'year_of_birth': '2021',
                    'address': 'abc address',
                    'contract_number': '112233',
                },
                'shipping_info': {
                    'recipient': 'John',
                    'address': 'test address',
                    'phone_number': '0909xxx',
                },
                'request_to': artist.id,
                'images': images,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.json(), {'images': ['Maximum 5 images are allowed.']})

    def test_should_pass_collector_request_certificate_when_edition_has_linked(self):
        medium = MediumArtworkFactory(category='painting', user=UserFactory())
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()

        linked_edition = ArtworkEditionFactory()

        artist = UserFactory(role=USER_ROLE.ARTIST)
        artwork = ArtworkFactory(owner=self.user, status='available', size=None, total_edition=3, title='Artwork 1')
        edition = ArtworkEditionFactory(edition_number=1, status='available', artwork=artwork,
                                        linked_edition=linked_edition)
        images = [
            'image_1.png',
            'image_2.png',
        ]

        response = self.client.post(
            f'/api/artwork/artwork/{artwork.uuid}/request_certificate/',
            {
                'artwork': {
                    'uuid': str(artwork.uuid),
                    'id': artwork.id,
                    'title': 'Mountain',
                    'size': {
                        'height': 1,
                        'width': 1,
                        'depth': 1,
                    },
                    'year_created': 2021,
                    'edition_number': 1,
                    'total_edition': 10,
                    'medium': {
                        'id': medium.id,
                        'name': medium.name,
                        'name_vi': medium.name_vi,
                        'category': medium.category,
                        'user': medium.user.id,
                    },
                },
                'edition': {
                    'id': edition.id,
                    'edition_number': 2,
                    'status': edition.status,
                    'location': edition.location.id,
                    'linked_edition': {
                        'id': linked_edition.id,
                        'edition_number': linked_edition.edition_number,
                    },
                },
                'owner_info': {
                    'name': 'John',
                    'year_of_birth': '2021',
                    'address': 'abc address',
                    'contract_number': '112233',
                },
                'shipping_info': {
                    'recipient': 'John',
                    'address': 'test address',
                    'phone_number': '0909xxx',
                },
                'request_to': artist.id,
                'images': images,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_delete_artwork(self):
        artwork_1 = ArtworkFactory(owner=self.user)
        ArtworkFactory(owner=self.user)
        ArtworkFactory(owner=self.user)

        response = self.client.delete(f'/api/artwork/artwork/{artwork_1.uuid}/', format='json')
        all_artwork = ArtWork.all_objects.count()

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(all_artwork, 2)

    def test_soft_delete_artwork_if_artwork_has_certificate(self):
        artwork_1 = ArtworkFactory(owner=self.user)
        ArtworkFactory(owner=self.user)
        ArtworkFactory(owner=self.user)

        ArtworkCertificateFactory(artwork_edition__artwork=artwork_1)

        response = self.client.delete(f'/api/artwork/artwork/{artwork_1.uuid}/', format='json')
        artwork_1.refresh_from_db()
        all_artwork = ArtWork.all_objects.count()
        active_artwork = ArtWork.objects.count()

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(all_artwork, 3)
        self.assertEqual(active_artwork, 2)
        self.assertFalse(artwork_1.active)

    def test_should_not_allow_delete_artwork_if_not_has_owner(self):
        artwork_1 = ArtworkFactory()

        response = self.client.delete(f'/api/artwork/artwork/{artwork_1.uuid}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'You do not have permission to delete this artwork.')

    def test_allow_user_create_custom_attribute_when_create_artwork(self):
        style = {
            'id': None,
            'name': 'New style',
        }
        data = self._create_data(style=style)
        response = self.client.post(
            '/api/artwork/artwork/',
            data=data,
            format='json',
        )

        style = StyleArtwork.objects.last()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['style']['id'], style.id)
        self.assertEqual(response.data['style']['name'], style.name)

    def test_allow_user_create_custom_attribute_when_update_artwork(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        artwork = ArtworkFactory(owner=self.user, status='available')

        style = {
            'id': None,
            'name': 'New style',
        }
        data = self._create_data(style=style)
        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/',
            data=data,
            format='json',
        )

        style = StyleArtwork.objects.last()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['style']['id'], style.id)
        self.assertEqual(response.data['style']['name'], style.name)

    def test_get_list_eligible_artwork(self):
        user = UserFactory()
        ArtworkFactory(owner=self.user, status='available')
        ArtworkFactory(owner=self.user, status='consignment')
        ArtworkFactory(owner=self.user, status='not_for_sale')
        ArtworkFactory(owner=user, status='sold')
        ArtworkFactory(owner=user, status='donated_gifted')

        response = self.client.get('/api/artwork/artwork/list_eligible_artwork/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 5)

    def test_artwork_filter_category(self):
        artwork_1 = ArtworkFactory(owner=self.user, category=CATEGORY_CHOICES[0][0])
        artwork_2 = ArtworkFactory(owner=self.user, category=CATEGORY_CHOICES[1][0])

        response = self.client.get('/api/artwork/artwork/', {
            'user_uuid': self.user.uuid,
            'category__in': 'sculpture,painting',
        })

        results = response.data['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], artwork_2.id)
        self.assertEqual(results[1]['id'], artwork_1.id)

    def test_artwork_filter_style(self):
        style_1 = StyleArtworkFactory()
        style_2 = StyleArtworkFactory()

        artwork_1 = ArtworkFactory(owner=self.user, style=style_1)
        artwork_2 = ArtworkFactory(owner=self.user, style=style_2)
        ArtworkFactory(owner=self.user)

        response = self.client.get('/api/artwork/artwork/', {
            'user_uuid': self.user.uuid,
            'style__in': f'{style_1.id},{style_2.id}',

        })

        results = response.data['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], artwork_2.id)
        self.assertEqual(results[1]['id'], artwork_1.id)

    def test_artwork_filter_price_range(self):
        ArtworkFactory(owner=self.user, price=1000)
        ArtworkFactory(owner=self.user, price=2000)
        ArtworkFactory(owner=self.user, price=3000)
        ArtworkFactory(owner=self.user, price=7000)
        ArtworkFactory(owner=self.user, price=11000)

        response = self.client.get('/api/artwork/artwork/', {
            'user_uuid': self.user.uuid,
            'price': '1000,5000',
            'ordering': 'price',
        })

        results = response.data['results']
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['price'], '1000.00')
        self.assertEqual(results[1]['price'], '2000.00')
        self.assertEqual(results[2]['price'], '3000.00')

    def test_artwork_filter_price_range_with_only_min_params(self):
        ArtworkFactory(owner=self.user, price=1000)
        ArtworkFactory(owner=self.user, price=2000)
        ArtworkFactory(owner=self.user, price=3000)
        ArtworkFactory(owner=self.user, price=7000)
        ArtworkFactory(owner=self.user, price=11000)

        response = self.client.get('/api/artwork/artwork/', {
            'user_uuid': self.user.uuid,
            'price': '3000',
            'ordering': 'price',
        })

        results = response.data['results']
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['price'], '3000.00')
        self.assertEqual(results[1]['price'], '7000.00')
        self.assertEqual(results[2]['price'], '11000.00')

    def test_artwork_filter_year_creation(self):
        artwork_1 = ArtworkFactory(owner=self.user, year_created=2000)
        artwork_2 = ArtworkFactory(owner=self.user, year_created=2010)
        ArtworkFactory(owner=self.user, year_created=2020)
        ArtworkFactory(owner=self.user, year_created=2024)

        response = self.client.get('/api/artwork/artwork/', {
            'user_uuid': self.user.uuid,
            'year': '1990, 2015',
        })

        results = response.data['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], artwork_2.id)
        self.assertEqual(results[1]['id'], artwork_1.id)

    def test_artwork_filter_artist(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()

        artist_artwork = ArtworkArtistFactory(create_user=self.user, artist_name='Tam')
        artwork_1 = ArtworkFactory(owner=self.user, artist_artwork=artist_artwork)

        artist = UserFactory(name='Tai', role=USER_ROLE.ARTIST)
        artwork_2 = ArtworkFactory(owner=self.user, price=2000)
        artwork_2.artist = artist
        artwork_2.save()

        ArtworkFactory(owner=self.user, price=3000)
        ArtworkFactory(owner=self.user, price=7000)
        ArtworkFactory(owner=self.user, price=11000)

        response = self.client.get('/api/artwork/artwork/', {
            'user_uuid': self.user.uuid,
            'artist': 'Tam,Tai',
        })

        results = response.data['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], artwork_2.id)
        self.assertEqual(results[1]['id'], artwork_1.id)

    def test_artwork_order_by_price_high_to_low(self):
        ArtworkFactory(owner=self.user, price=100)
        ArtworkFactory(owner=self.user, price=500)
        ArtworkFactory(owner=self.user, price=350)
        ArtworkFactory(owner=self.user, price=None)

        response = self.client.get('/api/artwork/artwork/', {
            'user_uuid': self.user.uuid,
            'ordering': '-price',
        })

        results = response.data['results']
        self.assertEqual(len(results), 4)

        self.assertEqual(results[0]['price'], '500.00')
        self.assertEqual(results[1]['price'], '350.00')
        self.assertEqual(results[2]['price'], '100.00')
        self.assertIsNone(results[3]['price'])

    def test_artwork_order_by_price_low_to_high(self):
        ArtworkFactory(owner=self.user, price=100)
        ArtworkFactory(owner=self.user, price=500)
        ArtworkFactory(owner=self.user, price=350)
        ArtworkFactory(owner=self.user, price=None)

        response = self.client.get('/api/artwork/artwork/', {
            'user_uuid': self.user.uuid,
            'ordering': 'price',
        })

        results = response.data['results']
        self.assertEqual(len(results), 4)

        self.assertEqual(results[0]['price'], '100.00')
        self.assertEqual(results[1]['price'], '350.00')
        self.assertEqual(results[2]['price'], '500.00')
        self.assertIsNone(results[3]['price'])

    def test_artist_request_certificate_edition_total_unique_and_status_available(self):
        artwork = ArtworkFactory(artist=self.user, status='available', size=None, total_edition=1)
        artwork_edition_1 = ArtworkEditionFactory(artwork=artwork, status='available')
        ArtworkEditionFactory(artwork__artist=self.user)
        new_user = UserFactory()
        issued_to_id = new_user.id

        response = self.client.post(
            f'/api/artwork/artwork/{artwork.id}/create_certificate/',
            {
                'edition_id': artwork_edition_1.id,
                'issued_to_id': issued_to_id,
                'owner_info': {
                    'name': 'John',
                    'year_of_birth': '2021',
                    'address': 'abc address',
                    'contract_number': '112233',
                },
                'shipping_info': {
                    'recipient': 'John',
                    'address': 'test address',
                    'phone_number': '0909xxx',
                },
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        certificate = ArtworkCertificate.objects.first()
        artwork_edition_1.refresh_from_db()
        artwork.refresh_from_db()

        self.assertEqual(certificate.issued_by, self.user)
        self.assertEqual(certificate.issued_to, new_user)
        self.assertEqual(artwork_edition_1.status, 'sold')
        self.assertEqual(artwork.status, 'sold')

    def test_artist_request_certificate_edition_total_unique_and_status_lost(self):
        artwork = ArtworkFactory(artist=self.user, status='available', size=None, total_edition=1)
        artwork_edition_1 = ArtworkEditionFactory(artwork=artwork, status='donated_gifted')
        ArtworkEditionFactory(artwork__artist=self.user)
        new_user = UserFactory()
        issued_to_id = new_user.id

        response = self.client.post(
            f'/api/artwork/artwork/{artwork.id}/create_certificate/',
            {
                'edition_id': artwork_edition_1.id,
                'issued_to_id': issued_to_id,
                'owner_info': {
                    'name': 'John',
                    'year_of_birth': '2021',
                    'address': 'abc address',
                    'contract_number': '112233',
                },
                'shipping_info': {
                    'recipient': 'John',
                    'address': 'test address',
                    'phone_number': '0909xxx',
                },
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        artwork_edition_1.refresh_from_db()
        artwork.refresh_from_db()

        self.assertEqual(artwork_edition_1.status, 'sold')

    def test_artist_request_certificate_edition_total_3_status_available(self):
        artwork = ArtworkFactory(artist=self.user, status='available', size=None, total_edition=3)
        artwork_edition_1 = ArtworkEditionFactory(artwork=artwork, status='available')
        ArtworkEditionFactory(artwork__artist=self.user)
        new_user = UserFactory()
        issued_to_id = new_user.id

        response = self.client.post(
            f'/api/artwork/artwork/{artwork.id}/create_certificate/',
            {
                'edition_id': artwork_edition_1.id,
                'issued_to_id': issued_to_id,
                'owner_info': {
                    'name': 'John',
                    'year_of_birth': '2021',
                    'address': 'abc address',
                    'contract_number': '112233',
                },
                'shipping_info': {
                    'recipient': 'John',
                    'address': 'test address',
                    'phone_number': '0909xxx',
                },
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        artwork_edition_1.refresh_from_db()
        artwork.refresh_from_db()

        self.assertEqual(artwork_edition_1.status, 'sold')
        self.assertEqual(artwork.status, 'sold')

    def test_get_list_artwork_same_collection_as_artist(self):
        user = UserFactory(role=USER_ROLE.ARTIST)
        ArtworkFactory(owner=user, status='available', year_created=2000)
        ArtworkFactory(owner=user, status='available', year_created=2000)
        ArtworkFactory(owner=user, status='available', year_created=2001)
        ArtworkFactory(owner=user, status='available', year_created=2005)
        artwork = ArtworkFactory(owner=user, status='available', year_created=2005)

        response = self.client.get('/api/artwork/artwork/list_artwork_same_collection/',
                                   {'user_id': user.id, 'year_created': 2000, 'artwork_id': artwork.id,
                                    'owner_id': user.id,
                                    },
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_get_list_artwork_same_collection_as_artist_with_year_created_none(self):
        user = UserFactory(role=USER_ROLE.ARTIST)
        artwork = ArtworkFactory(owner=user, status='available', year_created=2005)

        response = self.client.get('/api/artwork/artwork/list_artwork_same_collection/',
                                   {'user_id': user.id, 'artwork_id': artwork.id,
                                    'owner_id': user.id,
                                    },
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_get_list_artwork_same_collection_as_collector(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)

        ArtworkFactory(owner=artist, status='available', year_created=2000)
        ArtworkFactory(owner=artist, status='available', year_created=2001)
        ArtworkFactory(owner=artist, status='available', year_created=2005)
        ArtworkFactory(owner=artist, status='available', year_created=2005)

        response = self.client.get('/api/artwork/artwork/list_artwork_same_collection/',
                                   {'user_id': self.user.id,
                                    'owner_id': artist.id},
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_get_list_artwork_same_collection_as_gallery(self):
        user = UserFactory(role=USER_ROLE.GALLERY_OWNER)
        ArtworkFactory(owner=user, status='available', year_created=2000)
        artwork = ArtworkFactory(owner=user, status='available', year_created=2005)

        response = self.client.get('/api/artwork/artwork/list_artwork_same_collection/',
                                   {'user_id': user.id, 'year_created': '2000', 'artwork_id': artwork.id,
                                    'owner_id': user.id,
                                    },
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_get_list_artwork_same_collection_with_not_owner_id(self):
        user = UserFactory(role=USER_ROLE.GALLERY_OWNER)
        ArtworkFactory(owner=user, status='available', year_created=2000)
        artwork = ArtworkFactory(owner=user, status='available', year_created=2005)

        response = self.client.get('/api/artwork/artwork/list_artwork_same_collection/',
                                   {'user_id': user.id, 'year_created': '2000', 'artwork_id': artwork.id,
                                    },
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_get_list_artworks_for_selection(self):
        user = UserFactory()
        ArtworkFactory(owner=self.user, status='available')
        ArtworkFactory(owner=self.user, status='consignment')
        ArtworkFactory(owner=self.user, status='not_for_sale')
        ArtworkFactory(owner=user, status='sold')
        ArtworkFactory(owner=user, status='donated_gifted')

        response = self.client.get('/api/artwork/artwork/list_artworks_for_selection/',
                                   {'user_uuid': self.user.uuid}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)

    def test_create_artwork_with_collections(self):
        artwork_1 = ArtworkFactory(owner=self.user, status='available')
        artwork_2 = ArtworkFactory(owner=self.user, status='consignment')
        collection = CollectionFactory(owner=self.user, artworks=[artwork_1, artwork_2])

        data = self._create_data(collections=[collection.id])

        response = self.client.post(
            '/api/artwork/artwork/',
            data=data,
            format='json',
        )

        collection.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_get_list_artwork_excluding_sold_donated_gifted(self):
        user = UserFactory()
        available_artwork = ArtworkFactory(owner=user, status='available')
        consignment_artwork = ArtworkFactory(owner=user, status='consignment')
        not_for_sale_artwork = ArtworkFactory(owner=user, status='not_for_sale')
        sold_artwork = ArtworkFactory(owner=user, status='sold')
        donated_artwork = ArtworkFactory(owner=user, status='donated_gifted')

        response = self.client.get(
            f'/api/artwork/artwork/list_artwork_excluding_sold_donated_gifted/?user_uuid={user.uuid}', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
        returned_ids = [artwork['id'] for artwork in response.data['results']]
        self.assertIn(available_artwork.id, returned_ids)
        self.assertIn(consignment_artwork.id, returned_ids)
        self.assertIn(not_for_sale_artwork.id, returned_ids)
        self.assertNotIn(sold_artwork.id, returned_ids)
        self.assertNotIn(donated_artwork.id, returned_ids)

    def test_get_artwork_view_info(self):
        artwork = ArtworkFactory()

        response = self.client.get(
            f'/api/artwork/artwork/{artwork.uuid}/artwork_view_info/',
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], artwork.title)

    def test_artwork_filter_status(self):
        artwork_1 = ArtworkFactory(owner=self.user, status='sold')
        artwork_2 = ArtworkFactory(owner=self.user, status='sold')

        response = self.client.get('/api/artwork/artwork/', {
            'user_uuid': self.user.uuid,
            'status__in': 'sold',
        })

        results = response.data['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], artwork_2.id)
        self.assertEqual(results[1]['id'], artwork_1.id)

    def test_get_list_artwork_with_user_id(self):
        artwork_1 = ArtworkFactory(owner=self.user)
        artwork_2 = ArtworkFactory(owner=self.user)
        other_artist = UserFactory()
        ArtworkFactory(owner=other_artist)

        response = self.client.get('/api/artwork/artwork/', {
            'user_uuid': self.user.uuid,
        })

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]['id'], artwork_2.id)
        self.assertEqual(results[1]['id'], artwork_1.id)

    def test_get_list_artwork_no_user_id_or_uuid(self):
        ArtworkFactory(owner=self.user, status='sold', subject=None)
        ArtworkFactory(owner=self.user, status='sold')

        response = self.client.get('/api/artwork/artwork/')
        results = response.data['results']
        self.assertEqual(len(results), 0)

    def test_get_list_gallery_artwork_by_share_link_public(self):
        artwork = ArtworkFactory(owner=self.user, is_public=True)
        user = UserFactory()
        share_link = ShareLinkFactory(
            user=user,
            share_type='artwork',
            recipient_type='public',
        )
        share_link.artwork.add(artwork)

        response = self.client.get(
            '/api/artwork/artwork/list_gallery_artwork/',
            {
                'share_link_id': share_link.id,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], artwork.id)

    def test_get_list_gallery_artwork_not_owner_permission_denied(self):
        other_user = UserFactory()

        response = self.client.get(
            '/api/artwork/artwork/list_gallery_artwork/',
            {
                'user_uuid': str(other_user.uuid),
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'You do not have permission to access this artwork.')

    def test_get_list_gallery_artwork_by_share_link_password_required(self):
        artwork = ArtworkFactory(owner=self.user, is_public=True)
        user = UserFactory()
        share_link = ShareLinkFactory(
            user=user,
            share_type='artwork',
            recipient_type='public',
            password='secret123',
            shared_items=[{'id': artwork.id, 'type': 'artwork'}],
        )
        response = self.client.get(
            '/api/artwork/artwork/list_gallery_artwork/',
            {
                'share_link_id': share_link.id,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(response.data.get('requires_password'))

    def test_get_list_gallery_artwork_by_share_link_password_invalid(self):
        artwork = ArtworkFactory(owner=self.user, is_public=True)
        user = UserFactory()
        share_link = ShareLinkFactory(
            user=user,
            share_type='artwork',
            recipient_type='public',
            password='secret123',
            shared_items=[{'id': artwork.id, 'type': 'artwork'}],
        )
        response = self.client.get(
            '/api/artwork/artwork/list_gallery_artwork/',
            {
                'share_link_id': share_link.id,
                'password': 'wrong-password',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data.get('error'), 'Invalid password')

    def test_get_list_gallery_artwork_by_share_link_require_login(self):
        owner = UserFactory()
        artwork = ArtworkFactory(owner=owner, is_public=True)
        share_link = ShareLinkFactory(
            user=owner,
            share_type='artwork',
            recipient_type='specific',
            shared_items=[{'id': artwork.id, 'type': 'artwork'}],
        )
        self.client.credentials()
        response = self.client.get(
            '/api/artwork/artwork/list_gallery_artwork/',
            {
                'share_link_id': share_link.id,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(response.data.get('requires_login'))

    def test_get_list_gallery_artwork_by_share_link_password_match(self):
        artwork = ArtworkFactory(owner=self.user, is_public=True)
        user = UserFactory()
        share_link = ShareLinkFactory(
            user=user,
            share_type='artwork',
            recipient_type='public',
            password='secret123',
        )
        share_link.artwork.add(artwork)

        response = self.client.get(
            '/api/artwork/artwork/list_gallery_artwork/',
            {
                'share_link_id': share_link.id,
                'password': 'secret123',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], artwork.id)

    def test_get_list_gallery_artwork_by_share_link_recipient_user_not_match(self):
        artwork = ArtworkFactory(owner=self.user, is_public=True)
        user = UserFactory()
        share_link = ShareLinkFactory(
            user=user,
            share_type='artwork',
            recipient_type='specific',
            shared_items=[{'id': artwork.id, 'type': 'artwork'}],
        )
        share_link.add_recipient(user)
        response = self.client.get(
            '/api/artwork/artwork/list_gallery_artwork/',
            {
                'share_link_id': share_link.id,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'You do not have permission to access this share link')

    def test_should_not_allow_get_list_artwork_not_valid_share_link_status(self):
        artwork = ArtworkFactory(owner=self.user, is_public=True)
        user = UserFactory()
        share_link = ShareLinkFactory(
            user=user,
            share_type='artwork',
            recipient_type='specific',
            shared_items=[{'id': artwork.id, 'type': 'artwork'}],
            is_active=False,
        )
        share_link.add_recipient(user)
        response = self.client.get(
            '/api/artwork/artwork/list_gallery_artwork/',
            {
                'share_link_id': share_link.id,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'This share link is no longer valid')

    def test_get_list_gallery_artwork_by_share_link_recipient_denied(self):
        owner = UserFactory()
        artwork = ArtworkFactory(owner=owner, is_public=True)
        recipient = UserFactory()
        share_link = ShareLinkFactory(
            user=owner,
            share_type='artwork',
            recipient_type='specific',
            shared_items=[{'id': artwork.id, 'type': 'artwork'}],
        )
        share_link.add_recipient(recipient)
        response = self.client.get(
            '/api/artwork/artwork/list_gallery_artwork/',
            {
                'share_link_id': share_link.id,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'You do not have permission to access this share link')

    def test_get_list_gallery_artwork_by_share_link_owner_allowed(self):
        artwork = ArtworkFactory(owner=self.user, is_public=True)
        share_link = ShareLinkFactory(
            user=self.user,
            share_type='artwork',
            recipient_type='specific',
        )
        share_link.artwork.add(artwork)

        response = self.client.get(
            '/api/artwork/artwork/list_gallery_artwork/',
            {
                'share_link_id': share_link.id,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_get_list_gallery_artwork_by_owner(self):
        artwork = ArtworkFactory(owner=self.user, is_public=True)

        response = self.client.get(
            '/api/artwork/artwork/list_gallery_artwork/',
            {
                'user_uuid': self.user.uuid,
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], artwork.id)

    def test_get_list_artist_name_for_collector(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        artist_with_account = UserFactory(role=USER_ROLE.ARTIST)
        ArtworkFactory(owner=self.user, status='available', artist=artist_with_account)
        ArtworkFactory(owner=self.user, status='available', artist=artist_with_account)

        response = self.client.get(
            '/api/artwork/artwork/list_artist_name_for_collector/',
            {'user_uuid': self.user.uuid},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_get_list_artist_name_with_token_valid(self):
        valid_token = jwt.encode(
            {
                'user_uuid': str(self.user.uuid),
                'scope': 'create_share_link',
                'expires_at': (timezone.now() + timedelta(minutes=30)).timestamp(),
            },
            settings.SECRET_KEY,
            algorithm='HS256',
        )
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()

        artist_with_account = UserFactory(role=USER_ROLE.ARTIST)

        ArtworkFactory(owner=self.user, status='available', artist=artist_with_account)

        response = self.client.get(
            '/api/artwork/artwork/list_artist_name_for_collector/',
            {'user_uuid': self.user.uuid, 'token': valid_token},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_get_list_artist_name_with_token_valid_case_param_search(self):
        valid_token = jwt.encode(
            {
                'user_uuid': str(self.user.uuid),
                'scope': 'create_share_link',
                'expires_at': (timezone.now() + timedelta(minutes=30)).timestamp(),
            },
            settings.SECRET_KEY,
            algorithm='HS256',
        )
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        artist_with_account = UserFactory(role=USER_ROLE.ARTIST, name='Tam')
        ArtworkFactory(owner=self.user, status='available', artist=artist_with_account)

        response = self.client.get(
            '/api/artwork/artwork/list_artist_name_for_collector/',
            {'user_uuid': self.user.uuid, 'token': valid_token, 'search': 'Tam'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_get_list_artist_name_with_token_valid_case_param_ordering_year_of_birth(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        valid_token = jwt.encode(
            {
                'user_uuid': str(self.user.uuid),
                'scope': 'create_share_link',
                'expires_at': (timezone.now() + timedelta(minutes=30)).timestamp(),
            },
            settings.SECRET_KEY,
            algorithm='HS256',
        )
        artwork_artist_1 = ArtworkArtistFactory(artist_name='Tam', year_of_birth=2003, create_user=self.user)
        artwork_artist_2 = ArtworkArtistFactory(artist_name='Son', year_of_birth=1997, create_user=self.user)
        ArtworkFactory(owner=self.user, artist_artwork=artwork_artist_1)
        ArtworkFactory(owner=self.user, artist_artwork=artwork_artist_2)

        response = self.client.get(
            '/api/artwork/artwork/list_artist_name_for_collector/',
            {'user_uuid': self.user.uuid, 'token': valid_token, 'ordering': 'year_of_birth'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_get_list_artist_name_with_token_valid_case_param_ordering_year_of_birth_reverse(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        valid_token = jwt.encode(
            {
                'user_uuid': str(self.user.uuid),
                'scope': 'create_share_link',
                'expires_at': (timezone.now() + timedelta(minutes=30)).timestamp(),
            },
            settings.SECRET_KEY,
            algorithm='HS256',
        )
        artwork_artist_1 = ArtworkArtistFactory(artist_name='Tam', year_of_birth=2003, create_user=self.user)
        artwork_artist_2 = ArtworkArtistFactory(artist_name='Son', year_of_birth=1997, create_user=self.user)
        ArtworkFactory(owner=self.user, artist_artwork=artwork_artist_1)
        ArtworkFactory(owner=self.user, artist_artwork=artwork_artist_2)

        response = self.client.get(
            '/api/artwork/artwork/list_artist_name_for_collector/',
            {'user_uuid': self.user.uuid, 'token': valid_token, 'ordering': '-year_of_birth'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_get_list_artist_name_with_token_valid_case_param_ordering_alphabet_a_z(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        valid_token = jwt.encode(
            {
                'user_uuid': str(self.user.uuid),
                'scope': 'create_share_link',
                'expires_at': (timezone.now() + timedelta(minutes=30)).timestamp(),
            },
            settings.SECRET_KEY,
            algorithm='HS256',
        )
        artwork_artist_1 = ArtworkArtistFactory(artist_name='Tam', year_of_birth=2003, create_user=self.user)
        artwork_artist_2 = ArtworkArtistFactory(artist_name='Son', year_of_birth=1997, create_user=self.user)
        ArtworkFactory(owner=self.user, artist_artwork=artwork_artist_1)
        ArtworkFactory(owner=self.user, artist_artwork=artwork_artist_2)

        ArtworkFactory(
            owner=self.user, status='available', artist_name='Anonymous Artist',
        )

        response = self.client.get(
            '/api/artwork/artwork/list_artist_name_for_collector/',
            {'user_uuid': self.user.uuid, 'token': valid_token, 'ordering': 'alphabet'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_get_list_artist_name_with_token_valid_case_param_ordering_alphabet_z_a(self):
        self.user.role = USER_ROLE.COLLECTOR
        self.user.save()
        valid_token = jwt.encode(
            {
                'user_uuid': str(self.user.uuid),
                'scope': 'create_share_link',
                'expires_at': (timezone.now() + timedelta(minutes=30)).timestamp(),
            },
            settings.SECRET_KEY,
            algorithm='HS256',
        )
        artwork_artist_1 = ArtworkArtistFactory(artist_name='Tam', year_of_birth=2003, create_user=self.user)
        artwork_artist_2 = ArtworkArtistFactory(artist_name='Son', year_of_birth=1997, create_user=self.user)
        ArtworkFactory(owner=self.user, artist_artwork=artwork_artist_1)
        ArtworkFactory(owner=self.user, artist_artwork=artwork_artist_2)

        ArtworkFactory(
            owner=self.user, status='available', artist_name='Anonymous Artist',
        )

        response = self.client.get(
            '/api/artwork/artwork/list_artist_name_for_collector/',
            {'user_uuid': self.user.uuid, 'token': valid_token, 'ordering': '-alphabet'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)

    def test_get_list_artwork_by_artist_case_artist_uuid_with_is_owner(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)
        ArtworkFactory(owner=self.user, status='available', artist=artist)

        response = self.client.get(
            '/api/artwork/artwork/list_artwork_by_artist/',
            {'artist_uuid': artist.uuid, 'owner_uuid': self.user.uuid},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_get_list_artwork_by_artist_case_artist_uuid_with_is_not_owner(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)
        ArtworkFactory(owner=self.user, status='available', artist=artist, is_public=True)
        ArtworkFactory(owner=self.user, status='available', artist=artist, is_public=False)
        user = UserFactory()

        valid_token = jwt.encode(
            {
                'user_uuid': str(user.uuid),
                'scope': 'single_artist',
                'expires_at': (timezone.now() + timedelta(minutes=30)).timestamp(),
            },
            settings.SECRET_KEY,
            algorithm='HS256',
        )

        response = self.client.get(
            '/api/artwork/artwork/list_artwork_by_artist/',
            {'artist_uuid': artist.uuid, 'owner_uuid': user.uuid, 'token': valid_token},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_list_artwork_by_artist_case_artwork_artist_id_with_is_owner(self):
        artist = ArtworkArtistFactory(artist_name='Jon', year_of_birth=2000)
        artwork = ArtworkFactory(owner=self.user, status='available', artist_artwork=artist)

        response = self.client.get(
            '/api/artwork/artwork/list_artwork_by_artist/',
            {'artist_artwork_id': artist.id, 'owner_uuid': self.user.uuid},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], artwork.id)

    def test_get_list_artwork_by_artist_case_artwork_artist_id_with_is_not_owner(self):
        artist = ArtworkArtistFactory(artist_name='Jon', year_of_birth=2000)
        artwork = ArtworkFactory(owner=self.user, status='available', artist_artwork=artist, is_public=True)
        ArtworkFactory(owner=self.user, status='available', artist_artwork=artist, is_public=False)
        user = UserFactory()

        valid_token = jwt.encode(
            {
                'user_uuid': str(user.uuid),
                'scope': 'single_artist',
                'expires_at': (timezone.now() + timedelta(minutes=30)).timestamp(),
            },
            settings.SECRET_KEY,
            algorithm='HS256',
        )

        response = self.client.get(
            '/api/artwork/artwork/list_artwork_by_artist/',
            {'artist_artwork_id': artist.id, 'owner_uuid': user.uuid, 'token': valid_token},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], artwork.id)

    def test_get_list_artwork_by_artist_case_none(self):
        valid_token = jwt.encode(
            {
                'user_uuid': str(self.user.uuid),
                'scope': 'single_artist',
                'expires_at': (timezone.now() + timedelta(minutes=30)).timestamp(),
            },
            settings.SECRET_KEY,
            algorithm='HS256',
        )

        response = self.client.get(
            '/api/artwork/artwork/list_artwork_by_artist/',
            {'owner_uuid': self.user.uuid, 'token': valid_token},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_create_single_artist_token(self):
        user_uuid = str(self.user.uuid)

        response = self.client.get(
            '/api/artwork/artwork/create_single_artist_token/',
            {'user_uuid': user_uuid},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        token = response.data
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])

        self.assertEqual(payload['user_uuid'], user_uuid)
        self.assertEqual(payload['scope'], 'single_artist')
        self.assertTrue(payload['expires_at'] > timezone.now().timestamp())

    def test_get_list_special_artwork(self):
        ArtworkFactory(owner=self.user, status='available', year_created=2005)

        response = self.client.get(
            '/api/artwork/artwork/list_special_artwork/',
            {'user_uuid': self.user.uuid},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_artwork_edition_with_linked_edition_related_orphaned_certificate(self):
        artwork = ArtworkFactory(owner=self.user, status='available', total_edition=1)
        edition = ArtworkEditionFactory(artwork=artwork, edition_number=1)

        linked_artwork = ArtworkFactory(owner=self.user, status='available', total_edition=1)
        linked_edition = ArtworkEditionFactory(artwork=linked_artwork, edition_number=1)
        linked_certificate = ArtworkCertificateFactory(artwork_edition=linked_edition)

        linked_edition.linked_edition = edition
        linked_edition.save()

        self.assertIsNotNone(linked_edition.certificate)
        self.assertEqual(linked_edition.certificate.id, linked_certificate.id)

        linked_certificate.delete()

        edition.refresh_from_db()
        linked_edition.refresh_from_db()

        response = self.client.get(f'/api/artwork/artwork/{artwork.uuid}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        editions = response.data['editions']
        self.assertEqual(len(editions), 1)
        self.assertIsNone(editions[0]['id_certificate'])

    def test_get_id_certificate_edition_with_certificate(self):
        artwork = ArtworkFactory(owner=self.user, status='available', total_edition=1)
        edition = ArtworkEditionFactory(artwork=artwork, edition_number=1)
        certificate = ArtworkCertificateFactory(artwork_edition=edition)

        response = self.client.get(f'/api/artwork/artwork/{artwork.uuid}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        editions = response.data['editions']
        self.assertEqual(len(editions), 1)
        self.assertEqual(editions[0]['id_certificate'], certificate.code)

    def test_get_id_certificate_edition_without_certificate(self):
        artwork = ArtworkFactory(owner=self.user, status='available', total_edition=1)
        ArtworkEditionFactory(artwork=artwork, edition_number=1)

        response = self.client.get(f'/api/artwork/artwork/{artwork.uuid}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        editions = response.data['editions']
        self.assertEqual(len(editions), 1)
        self.assertIsNone(editions[0]['id_certificate'])

    def test_get_id_certificate_from_linked_edition_related(self):
        artwork = ArtworkFactory(owner=self.user, status='available', total_edition=1)
        edition = ArtworkEditionFactory(artwork=artwork, edition_number=1)

        linked_artwork = ArtworkFactory(owner=self.user, status='available', total_edition=1)
        linked_edition = ArtworkEditionFactory(artwork=linked_artwork, edition_number=1)
        linked_certificate = ArtworkCertificateFactory(artwork_edition=linked_edition)

        linked_edition.linked_edition = edition
        linked_edition.save()

        response = self.client.get(f'/api/artwork/artwork/{artwork.uuid}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        editions = response.data['editions']
        self.assertEqual(len(editions), 1)
        self.assertEqual(editions[0]['id_certificate'], linked_certificate.code)

    def test_get_id_certificate_from_linked_edition(self):
        artwork = ArtworkFactory(owner=self.user, status='available', total_edition=1)
        edition = ArtworkEditionFactory(artwork=artwork, edition_number=1)

        linked_artwork = ArtworkFactory(owner=self.user, status='available', total_edition=1)
        linked_edition = ArtworkEditionFactory(artwork=linked_artwork, edition_number=1)
        linked_certificate = ArtworkCertificateFactory(artwork_edition=linked_edition)

        edition.linked_edition = linked_edition
        edition.save()

        response = self.client.get(f'/api/artwork/artwork/{artwork.uuid}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        editions = response.data['editions']
        self.assertEqual(len(editions), 1)
        self.assertEqual(editions[0]['id_certificate'], linked_certificate.code)

    def test_get_id_certificate_priority_order(self):
        artwork = ArtworkFactory(owner=self.user, status='available', total_edition=1)
        edition = ArtworkEditionFactory(artwork=artwork, edition_number=1)
        main_certificate = ArtworkCertificateFactory(artwork_edition=edition)

        linked_artwork = ArtworkFactory(owner=self.user, status='available', total_edition=1)
        linked_edition = ArtworkEditionFactory(artwork=linked_artwork, edition_number=1)
        ArtworkCertificateFactory(artwork_edition=linked_edition)

        edition.linked_edition = linked_edition
        edition.save()

        response = self.client.get(f'/api/artwork/artwork/{artwork.uuid}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        editions = response.data['editions']
        self.assertEqual(len(editions), 1)
        self.assertEqual(editions[0]['id_certificate'], main_certificate.code)

    def test_get_id_certificate_no_linked_edition_related(self):
        artwork = ArtworkFactory(owner=self.user, status='available', total_edition=1)
        edition = ArtworkEditionFactory(artwork=artwork, edition_number=1)

        self.assertFalse(hasattr(edition, 'linked_edition_related') and edition.linked_edition_related)

        response = self.client.get(f'/api/artwork/artwork/{artwork.uuid}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        editions = response.data['editions']
        self.assertEqual(len(editions), 1)
        self.assertIsNone(editions[0]['id_certificate'])

    def test_get_id_certificate_no_linked_edition(self):
        artwork = ArtworkFactory(owner=self.user, status='available', total_edition=1)
        edition = ArtworkEditionFactory(artwork=artwork, edition_number=1)

        self.assertFalse(hasattr(edition, 'linked_edition') and edition.linked_edition)

        response = self.client.get(f'/api/artwork/artwork/{artwork.uuid}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        editions = response.data['editions']
        self.assertEqual(len(editions), 1)
        self.assertIsNone(editions[0]['id_certificate'])

    def test_get_id_certificate_linked_edition_related_without_certificate(self):
        artwork = ArtworkFactory(owner=self.user, status='available', total_edition=1)
        edition = ArtworkEditionFactory(artwork=artwork, edition_number=1)

        linked_artwork = ArtworkFactory(owner=self.user, status='available', total_edition=1)
        linked_edition = ArtworkEditionFactory(artwork=linked_artwork, edition_number=1)

        linked_edition.linked_edition = edition
        linked_edition.save()

        self.assertTrue(hasattr(edition, 'linked_edition_related'))
        self.assertFalse(hasattr(edition.linked_edition_related, 'certificate'))

        response = self.client.get(f'/api/artwork/artwork/{artwork.uuid}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        editions = response.data['editions']
        self.assertEqual(len(editions), 1)
        self.assertIsNone(editions[0]['id_certificate'])

    def test_get_id_certificate_linked_edition_without_certificate(self):
        artwork = ArtworkFactory(owner=self.user, status='available', total_edition=1)
        edition = ArtworkEditionFactory(artwork=artwork, edition_number=1)

        linked_artwork = ArtworkFactory(owner=self.user, status='available', total_edition=1)
        linked_edition = ArtworkEditionFactory(artwork=linked_artwork, edition_number=1)

        edition.linked_edition = linked_edition
        edition.save()

        self.assertTrue(hasattr(edition, 'linked_edition') and edition.linked_edition)
        self.assertFalse(hasattr(edition.linked_edition, 'certificate') and edition.linked_edition.certificate)

        response = self.client.get(f'/api/artwork/artwork/{artwork.uuid}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        editions = response.data['editions']
        self.assertEqual(len(editions), 1)
        self.assertIsNone(editions[0]['id_certificate'])

    def test_get_certificate_code_safely_with_valid_certificate(self):
        artwork = ArtworkFactory(owner=self.user, status='available', total_edition=1)
        edition = ArtworkEditionFactory(artwork=artwork, edition_number=1)
        certificate = ArtworkCertificateFactory(artwork_edition=edition)

        response = self.client.get(f'/api/artwork/artwork/{artwork.uuid}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        editions = response.data['editions']
        self.assertEqual(len(editions), 1)
        self.assertEqual(editions[0]['id_certificate'], certificate.code)

    def test_get_certificate_code_safely_without_certificate(self):
        artwork = ArtworkFactory(owner=self.user, status='available', total_edition=1)
        ArtworkEditionFactory(artwork=artwork, edition_number=1)

        response = self.client.get(f'/api/artwork/artwork/{artwork.uuid}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        editions = response.data['editions']
        self.assertEqual(len(editions), 1)
        self.assertIsNone(editions[0]['id_certificate'])

    def test_get_certificate_code_safely_with_orphaned_certificate(self):
        artwork = ArtworkFactory(owner=self.user, status='available', total_edition=1)
        edition = ArtworkEditionFactory(artwork=artwork, edition_number=1)
        certificate = ArtworkCertificateFactory(artwork_edition=edition)

        certificate.delete()
        edition.refresh_from_db()

        response = self.client.get(f'/api/artwork/artwork/{artwork.uuid}/', format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        editions = response.data['editions']
        self.assertEqual(len(editions), 1)
        self.assertIsNone(editions[0]['id_certificate'])

    def test_list_artwork_in_stock_should_return_only_in_stock_status(self):
        artwork_in_stock = ArtworkFactory(owner=self.user, status='in_stock')
        ArtworkFactory(owner=self.user, status='available')

        response = self.client.get(
            '/api/artwork/artwork/list_artwork_in_stock/',
            {'user_uuid': self.user.uuid},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['id'], artwork_in_stock.id)
        self.assertEqual(results[0]['status']['key'], 'in_stock')

    def test_update_artwork_in_stock_success(self):
        artwork = ArtworkFactory(owner=self.user, status='in_stock')
        new_location = UserLocationFactory(user=self.user)

        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/update_artwork_in_stock/',
            {
                'status': 'available',
                'inventory_code': 'INV-001',
                'location': new_location.id,
                'is_public_certificate': True,
            },
            format='json',
        )

        artwork.refresh_from_db()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(artwork.status, 'available')
        self.assertEqual(artwork.inventory_code, 'INV-001')
        self.assertEqual(artwork.location, new_location)
        self.assertTrue(artwork.is_public_certificate)

    def test_update_artwork_in_stock_only_for_in_stock_status(self):
        artwork = ArtworkFactory(owner=self.user, status='available')

        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/update_artwork_in_stock/',
            {
                'status': 'in_stock',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Artwork must be in stock to update.', str(response.data))

    def test_update_artwork_in_stock_not_owner(self):
        other_user = UserFactory()
        artwork = ArtworkFactory(owner=other_user, status='in_stock')

        response = self.client.patch(
            f'/api/artwork/artwork/{artwork.uuid}/update_artwork_in_stock/',
            {
                'status': 'available',
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'You do not have permission to edit this artwork.')

    def test_get_list_artist_name_for_collector_not_owner_without_token_permission_denied(self):
        other_user = UserFactory(role=USER_ROLE.COLLECTOR)
        ArtworkFactory(owner=other_user, status='available')

        response = self.client.get(
            '/api/artwork/artwork/list_artist_name_for_collector/',
            {'user_uuid': str(other_user.uuid)},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['detail'], 'You do not have permission to access this artist list.')

    def test_get_create_share_link(self):
        ArtworkFactory(owner=self.user, status='available')

        response = self.client.get('/api/artwork/artwork/create_share_link/',
                                   {'user_uuid': self.user.uuid}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_disable_certificate_sync_sets_flag_and_is_idempotent(self):
        artwork = ArtworkFactory(owner=self.user)
        artwork.is_certificate_sync_disabled = False
        artwork.save(update_fields=['is_certificate_sync_disabled'])

        artwork.disable_certificate_sync()
        artwork.refresh_from_db()
        self.assertTrue(artwork.is_certificate_sync_disabled)

        artwork.disable_certificate_sync()
        artwork.refresh_from_db()
        self.assertTrue(artwork.is_certificate_sync_disabled)

    def test_has_transferred_certificate_self_and_can_sync_certificates_false(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)
        collector = UserFactory(role=USER_ROLE.COLLECTOR)
        artwork = ArtworkFactory(owner=artist)
        edition = ArtworkEditionFactory(artwork=artwork)
        ArtworkCertificateFactory(artwork_edition=edition, issued_by=artist, issued_to=collector)

        self.assertTrue(artwork.has_transferred_certificate())
        self.assertFalse(artwork.can_sync_certificates())

    def test_has_transferred_certificate_from_linked_artwork(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)
        collector = UserFactory(role=USER_ROLE.COLLECTOR)
        linked_artwork = ArtworkFactory(owner=artist)
        linked_edition = ArtworkEditionFactory(artwork=linked_artwork)
        ArtworkCertificateFactory(artwork_edition=linked_edition, issued_by=artist, issued_to=collector)

        artwork = ArtworkFactory(owner=artist, linked_artwork=linked_artwork)

        self.assertTrue(artwork.has_transferred_certificate())
        self.assertFalse(artwork.can_sync_certificates())

    def test_has_transferred_certificate_from_linked_artworks_reverse_relation(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)
        collector = UserFactory(role=USER_ROLE.COLLECTOR)
        artwork = ArtworkFactory(owner=artist)
        child_artwork = ArtworkFactory(owner=artist, linked_artwork=artwork)
        child_edition = ArtworkEditionFactory(artwork=child_artwork)
        ArtworkCertificateFactory(artwork_edition=child_edition, issued_by=artist, issued_to=collector)

        self.assertTrue(artwork.has_transferred_certificate())
        self.assertFalse(artwork.can_sync_certificates())

    def test_has_transferred_certificate_linked_artwork_exists_but_not_transferred(self):
        artist = UserFactory(role=USER_ROLE.ARTIST)
        linked_artwork = ArtworkFactory(owner=artist)
        linked_edition = ArtworkEditionFactory(artwork=linked_artwork)
        ArtworkCertificateFactory(artwork_edition=linked_edition, issued_by=artist, issued_to=artist)

        artwork = ArtworkFactory(owner=artist, linked_artwork=linked_artwork)

        self.assertFalse(artwork.has_transferred_certificate())
        self.assertTrue(artwork.can_sync_certificates())


class InventoryCodeTest(BaseUserTest):
    def setUp(self) -> None:
        super().setUp()
        self.user.role = USER_ROLE.ARTIST
        self.user.save()

    def test_get_category_code_with_painting(self):
        from artwork.utils.inventory_code import get_category_code

        result = get_category_code('painting')
        self.assertEqual(result, 'P')

    def test_get_category_code_with_sculpture(self):
        from artwork.utils.inventory_code import get_category_code

        result = get_category_code('sculpture')
        self.assertEqual(result, 'S')

    def test_get_category_code_with_unknown_category(self):
        from artwork.utils.inventory_code import get_category_code

        result = get_category_code('drawing')
        self.assertEqual(result, 'D')

    def test_get_category_code_with_empty_category(self):
        from artwork.utils.inventory_code import get_category_code

        result = get_category_code('')
        self.assertEqual(result, 'NULL')

    def test_get_category_code_with_none_category(self):
        from artwork.utils.inventory_code import get_category_code

        result = get_category_code(None)
        self.assertEqual(result, 'NULL')

    def test_get_name_code_with_valid_object(self):
        from artwork.utils.inventory_code import get_name_code

        class MockObject:
            def __init__(self, name):
                self.name = name

        obj = MockObject('Oil Paint')
        result = get_name_code(obj)
        self.assertEqual(result, 'Oil Paint')

    def test_get_name_code_with_none_object(self):
        from artwork.utils.inventory_code import get_name_code

        result = get_name_code(None)
        self.assertEqual(result, 'NULL')

    def test_get_name_code_with_object_no_name_attribute(self):
        from artwork.utils.inventory_code import get_name_code

        class MockObject:
            pass

        obj = MockObject()
        result = get_name_code(obj)
        self.assertEqual(result, 'NULL')

    def test_get_name_code_with_object_empty_name(self):
        from artwork.utils.inventory_code import get_name_code

        class MockObject:
            def __init__(self, name):
                self.name = name

        obj = MockObject('')
        result = get_name_code(obj)
        self.assertEqual(result, 'NULL')

    def test_get_name_code_with_object_none_name(self):
        from artwork.utils.inventory_code import get_name_code

        class MockObject:
            def __init__(self, name):
                self.name = name

        obj = MockObject(None)
        result = get_name_code(obj)
        self.assertEqual(result, 'NULL')

    def test_get_subjects_code_with_valid_subjects(self):
        from artwork.utils.inventory_code import get_subjects_code

        class MockSubject:
            def __init__(self, name):
                self.name = name

        class MockQuerySet:
            def __init__(self, subjects):
                self.subjects = subjects

            def exists(self):
                return len(self.subjects) > 0

            def first(self):
                return self.subjects[0] if self.subjects else None

        subjects = MockQuerySet([MockSubject('Portrait')])
        result = get_subjects_code(subjects)
        self.assertEqual(result, 'Portrait')

    def test_get_subjects_code_with_empty_subjects(self):
        from artwork.utils.inventory_code import get_subjects_code

        class MockQuerySet:
            def exists(self):
                return True

            def first(self):
                return None

        subjects = MockQuerySet()
        result = get_subjects_code(subjects)
        self.assertEqual(result, 'NULL')

    def test_get_subjects_code_with_none_subjects(self):
        from artwork.utils.inventory_code import get_subjects_code

        result = get_subjects_code(None)
        self.assertEqual(result, 'NULL')

    def test_get_subjects_code_with_subject_no_name(self):
        from artwork.utils.inventory_code import get_subjects_code

        class MockSubject:
            pass

        class MockQuerySet:
            def __init__(self, subjects):
                self.subjects = subjects

            def exists(self):
                return len(self.subjects) > 0

            def first(self):
                return self.subjects[0] if self.subjects else None

        subjects = MockQuerySet([MockSubject()])
        result = get_subjects_code(subjects)
        self.assertEqual(result, 'NULL')

    def test_get_year_code_with_valid_year(self):
        from artwork.utils.inventory_code import get_year_code

        result = get_year_code(2023)
        self.assertEqual(result, '2023')

    def test_get_year_code_with_none_year(self):
        from artwork.utils.inventory_code import get_year_code

        result = get_year_code(None)
        self.assertEqual(result, 'NULL')

    def test_get_year_code_with_zero_year(self):
        from artwork.utils.inventory_code import get_year_code

        result = get_year_code(0)
        self.assertEqual(result, 'NULL')

    def test_get_artist_name_code_with_artist_legal_name(self):
        from artwork.utils.inventory_code import get_artist_name_code

        class MockArtist:
            def __init__(self, legal_name):
                self.legal_name = legal_name

        class MockArtwork:
            def __init__(self, artist, artist_artwork=None):
                self.artist = artist
                self.artist_artwork = artist_artwork

        artist = MockArtist('John Doe')
        artwork = MockArtwork(artist)
        result = get_artist_name_code(artwork)
        self.assertEqual(result, 'JOHNDOE')

    def test_get_artist_name_code_with_artist_artwork_name(self):
        from artwork.utils.inventory_code import get_artist_name_code

        class MockArtist:
            def __init__(self, legal_name):
                self.legal_name = legal_name

        class MockArtistArtwork:
            def __init__(self, artist_name):
                self.artist_name = artist_name

        class MockArtwork:
            def __init__(self, artist, artist_artwork):
                self.artist = artist
                self.artist_artwork = artist_artwork

        artist = MockArtist('')
        artist_artwork = MockArtistArtwork('Jane Smith')
        artwork = MockArtwork(artist, artist_artwork)
        result = get_artist_name_code(artwork)
        self.assertEqual(result, 'JANESMITH')

    def test_get_artist_name_code_with_no_artist_info(self):
        from artwork.utils.inventory_code import get_artist_name_code

        class MockArtwork:
            def __init__(self):
                self.artist = None
                self.artist_artwork = None

        artwork = MockArtwork()
        result = get_artist_name_code(artwork)
        self.assertEqual(result, 'NULL')

    def test_get_artist_name_code_with_spaces_in_name(self):
        from artwork.utils.inventory_code import get_artist_name_code

        class MockArtist:
            def __init__(self, legal_name):
                self.legal_name = legal_name

        class MockArtwork:
            def __init__(self, artist):
                self.artist = artist
                self.artist_artwork = None

        artist = MockArtist('Van Gogh Vincent')
        artwork = MockArtwork(artist)
        result = get_artist_name_code(artwork)
        self.assertEqual(result, 'VANGOGHVINCENT')

    def test_get_artwork_id_code_with_valid_id(self):
        from artwork.utils.inventory_code import get_artwork_id_code

        result = get_artwork_id_code(12345)
        self.assertEqual(result, '12345')

    def test_get_artwork_id_code_with_string_id(self):
        from artwork.utils.inventory_code import get_artwork_id_code

        result = get_artwork_id_code('abc123')
        self.assertEqual(result, 'abc123')

    def test_generate_inventory_code_complete_artwork(self):
        from artwork.utils.inventory_code import generate_inventory_code

        class MockArtist:
            def __init__(self, legal_name):
                self.legal_name = legal_name

        class MockMedium:
            def __init__(self, name):
                self.name = name

        class MockSubject:
            def __init__(self, name):
                self.name = name

        class MockQuerySet:
            def __init__(self, subjects):
                self.subjects = subjects

            def exists(self):
                return len(self.subjects) > 0

            def first(self):
                return self.subjects[0] if self.subjects else None

        class MockArtwork:
            def __init__(self):
                self.category = 'painting'
                self.subjects = MockQuerySet([MockSubject('Portrait')])
                self.medium = MockMedium('Oil Paint')
                self.year_created = 2023
                self.artist = MockArtist('John Doe')
                self.artist_artwork = None
                self.id = 12345

        artwork = MockArtwork()
        result = generate_inventory_code(artwork)
        self.assertEqual(result, 'P-Portrait-Oil Paint-2023-JOHNDOE-12345')

    def test_generate_inventory_code_minimal_artwork(self):
        from artwork.utils.inventory_code import generate_inventory_code

        class MockQuerySet:
            def exists(self):
                return True

            def first(self):
                return None

        class MockArtwork:
            def __init__(self):
                self.category = None
                self.subjects = MockQuerySet()
                self.medium = None
                self.year_created = None
                self.artist = None
                self.artist_artwork = None
                self.id = 999

        artwork = MockArtwork()
        result = generate_inventory_code(artwork)
        self.assertEqual(result, 'NULL-NULL-NULL-NULL-NULL-999')

    def test_generate_inventory_code_partial_artwork(self):
        from artwork.utils.inventory_code import generate_inventory_code

        class MockMedium:
            def __init__(self, name):
                self.name = name

        class MockQuerySet:
            def exists(self):
                return True

            def first(self):
                return None

        class MockArtwork:
            def __init__(self):
                self.category = 'sculpture'
                self.subjects = MockQuerySet()
                self.medium = MockMedium('Bronze')
                self.year_created = 2022
                self.artist = None
                self.artist_artwork = None
                self.id = 555

        artwork = MockArtwork()
        result = generate_inventory_code(artwork)
        self.assertEqual(result, 'S-NULL-Bronze-2022-NULL-555')

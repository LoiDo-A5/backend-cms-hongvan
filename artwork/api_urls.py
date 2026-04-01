from django.urls import path
from rest_framework import routers

from artwork.api.artist_tag_request import ArtistTagRequestViewSet
from artwork.api.artwork import ArtworkViewSet
from artwork.api.artwork_count import ArtworkCountApi
from artwork.api.exhibition_count import ExhibitionCountApi
from artwork.api.artist_count import ArtistCountApi
from artwork.api.artwork_edition import ArtworkEditionApi
from artwork.api.artwork_edition_bulk_update import ArtworkEditionBulkUpdateApi
from artwork.api.artwork_edition_delete import ArtworkEditionDeleteAPIView
from artwork.api.artwork_edition_detail import ArtworkEditionDetailApi
from artwork.api.artwork_certificate import ArtworkCertificateApi
from artwork.api.category import CategoryArtworkApi
from artwork.api.collection import CollectionViewSet
from artwork.api.collection_count import CollectionCountApi
from artwork.api.currency import CurrencyArtworkApi
from artwork.api.certificate_request import CertificateRequestViewSet
from artwork.api.exhibition import ExhibitionViewSet
from artwork.api.filter_location_by_user import FilterLocationApi
from artwork.api.list_certificate_request import ListCertificateRequestApi
from artwork.api.share_link import ShareLinkViewSet
from artwork.api.signature_extraction import SignatureExtraction
from artwork.api.status import StatusArtworkApi
from artwork.api.color import ColorArtworkApi
from artwork.api.medium import MediumArtworkApi
from artwork.api.orientation import OrientationArtworkApi
from artwork.api.style import StyleArtworkApi
from artwork.api.subject import SubjectArtworkApi
from artwork.api.status_can_request_certificate import StatusCanRequestCertificateApi
from artwork.api.search_autocomplete import SearchAutocomplete
from artwork.api.filter_artist import FilterArtistByUserApi
from artwork.api.verify_qr_codes import VerifyQrCodes
from artwork.api.user_artist import UserArtistApi
from artwork.api.transfer_owner import (TransferOwnerApi, TransferOwnerWithRoleArtistApi,
                                        TransferOwnerArtworkWithRoleArtistApi)
from artwork.api.artwork_condition_images import ArtworkConditionImagesApi
from artwork.api.share_link_recipient import (
    ShareLinkRecipientListAPIView,
    ShareLinkRecipientListTypeArtworkAPIView,
)
from artwork.api.share_link_access import ShareLinkAccessAPIView
from artwork.api.manage_share_link import (
    ExtendShareLinkAPIView,
    ManageShareLinkListAPIView,
    RevokeShareLinkAPIView,
)

router = routers.SimpleRouter()
router.register(r'artwork', ArtworkViewSet)
router.register(r'certificate_request', CertificateRequestViewSet)
router.register(r'artist_tag_request', ArtistTagRequestViewSet)
router.register(r'collection', CollectionViewSet)
router.register(r'exhibition', ExhibitionViewSet)
router.register(r'share_links', ShareLinkViewSet, basename='share_link')

urlpatterns = [
    path('status/', StatusArtworkApi.as_view()),
    path('status/can_request_certificate/', StatusCanRequestCertificateApi.as_view()),
    path('currency/', CurrencyArtworkApi.as_view()),
    path('category/', CategoryArtworkApi.as_view()),

    path('filters/style/', StyleArtworkApi.as_view()),
    path('filters/subject/', SubjectArtworkApi.as_view()),
    path('filters/medium/', MediumArtworkApi.as_view()),
    path('filters/color/', ColorArtworkApi.as_view()),
    path('filters/orientation/', OrientationArtworkApi.as_view()),
    path('filters/artist_by_user/', FilterArtistByUserApi.as_view()),
    path('filters/location/', FilterLocationApi.as_view()),
    path('signature_extraction/', SignatureExtraction.as_view()),
    path('edition/', ArtworkEditionApi.as_view()),
    path('edition/<int:pk>/', ArtworkEditionDetailApi.as_view()),
    path('certificate/', ArtworkCertificateApi.as_view()),
    path('list_certificate_request/', ListCertificateRequestApi.as_view()),
    path('search_autocomplete/', SearchAutocomplete.as_view()),
    path('editions/bulk_update/', ArtworkEditionBulkUpdateApi.as_view()),
    path('verify_qr_codes/', VerifyQrCodes.as_view()),
    path('certificate/<uuid:code>/transfer_owner/', TransferOwnerApi.as_view()),
    path('certificate/<uuid:code>/transfer_owner_role_artist/', TransferOwnerWithRoleArtistApi.as_view()),
    path('transfer_owner_artwork_role_artist/', TransferOwnerArtworkWithRoleArtistApi.as_view()),
    path('collection_count/', CollectionCountApi.as_view()),
    path('artwork_count/', ArtworkCountApi.as_view()),
    path('exhibition_count/', ExhibitionCountApi.as_view()),
    path('artist_count/', ArtistCountApi.as_view()),
    path('edition/<int:pk>/delete/', ArtworkEditionDeleteAPIView.as_view()),
    path('user/artist/<str:identifier>/', UserArtistApi.as_view()),
    path('artwork/<int:artwork_id>/condition_images/', ArtworkConditionImagesApi.as_view()),

    path(
        'manage_share_links/',
        ManageShareLinkListAPIView.as_view(),
        name='manage_share_link_list',
    ),
    path(
        'manage_share_links/<uuid:pk>/revoke/',
        RevokeShareLinkAPIView.as_view(),
        name='manage_share_link_revoke',
    ),
    path(
        'manage_share_links/<uuid:pk>/extend/',
        ExtendShareLinkAPIView.as_view(),
        name='manage_share_link_extend',
    ),
    path(
        'share/<uuid:pk>/',
        ShareLinkAccessAPIView.as_view(),
        name='share_link_access',
    ),
    path(
        'share_link/user/<int:pk>/recipient/',
        ShareLinkRecipientListAPIView.as_view(),
        name='share_link_recipient_list',
    ),
    path(
        'share_link/user/<int:pk>/recipient/<int:recipient_id>/',
        ShareLinkRecipientListAPIView.as_view(),
    ),
    path('share_link/user/<int:pk>/recipient_type_artwork/', ShareLinkRecipientListTypeArtworkAPIView.as_view(),
         name='share_link_recipient_list_type_artwork'),
    path(
        'share_link/user/<int:pk>/recipient_type_artwork/<int:recipient_id>/',
        ShareLinkRecipientListTypeArtworkAPIView.as_view(),
        name='share_link_recipient_remove_type_artwork',
    ),
]

urlpatterns += router.urls

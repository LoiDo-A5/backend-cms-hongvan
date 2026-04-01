from django.contrib import admin

from artwork.admin.artist_tag_request import ArtistTagRequestAdmin
from artwork.admin.artwork_admin import ArtWorkAdmin
from artwork.admin.artwork_artist_admin import ArtworkArtistAdmin
from artwork.admin.share_link_admin import ShareLinkAdmin
from artwork.admin.artwork_certificate_admin import ArtworkCertificateAdmin
from artwork.admin.artwork_edition_admin import ArtworkEditionAdmin
from artwork.admin.certificate_request_admin import CertificateRequestAdmin
from artwork.admin.collection_admin import CollectionAdmin
from artwork.admin.color_artwork_admin import ColorArtworkAdmin
from artwork.admin.exhibition_admin import ExhibitionAdmin
from artwork.admin.exhibition_group_admin import ExhibitionGroupAdmin
from artwork.admin.image_artwork_admin import ImageArtworkAdmin
from artwork.admin.image_certificate_request_admin import ImageCertificateRequestAdmin
from artwork.admin.like_artwork_admin import LikeArtworkAdmin
from artwork.admin.like_collection import LikeCollectionAdmin
from artwork.admin.medium_artwork_admin import MediumArtworkAdmin
from artwork.admin.orientation_artwork_admin import OrientationArtworkAdmin
from artwork.admin.owner_certificate_admin import OwnerCertificateAdmin
from artwork.admin.shipping_certificate_admin import ShippingCertificateAdmin
from artwork.admin.size_artwork_admin import SizeArtworkAdmin
from artwork.admin.style_artwork_admin import StyleArtworkAdmin
from artwork.admin.subject_artwork_admin import SubjectArtworkAdmin
from artwork.admin.collector_ownership_transfer_admin import CollectorOwnershipTransferAdmin
from artwork.admin.comment_artwork_admin import CommentArtworkAdmin
from artwork.models import ArtworkCertificate, LikeCollection, LikeArtwork, Exhibition, ExhibitionGroup
from artwork.models import CertificateShipping
from artwork.models import OwnerCertificate
from artwork.models import ArtworkEdition
from artwork.models.artwork import ArtWork
from artwork.models.artwork_artist import ArtworkArtist
from artwork.models.color_artwork import ColorArtwork
from artwork.models.image_artwork import ImageArtwork
from artwork.models.image_certificate_request import ImageCertificateRequest
from artwork.models.medium_artwork import MediumArtwork
from artwork.models.orientation_artwork import OrientationArtwork
from artwork.models.size_artwork import SizeArtwork
from artwork.models.style_artwork import StyleArtwork
from artwork.models.subject_artwork import SubjectArtwork
from artwork.models.certificate_request import CertificateRequest
from artwork.models import ArtistTagRequest
from artwork.models import Collection
from artwork.models import CommentArtwork
from artwork.models import ShareLink
from artwork.models.collector_ownership_transfer import CollectorOwnershipTransfer

admin.site.register(ArtWork, ArtWorkAdmin)
admin.site.register(StyleArtwork, StyleArtworkAdmin)
admin.site.register(SubjectArtwork, SubjectArtworkAdmin)
admin.site.register(MediumArtwork, MediumArtworkAdmin)
admin.site.register(SizeArtwork, SizeArtworkAdmin)
admin.site.register(OrientationArtwork, OrientationArtworkAdmin)
admin.site.register(ColorArtwork, ColorArtworkAdmin)
admin.site.register(ImageArtwork, ImageArtworkAdmin)
admin.site.register(ArtworkCertificate, ArtworkCertificateAdmin)
admin.site.register(ArtworkEdition, ArtworkEditionAdmin)
admin.site.register(OwnerCertificate, OwnerCertificateAdmin)
admin.site.register(CertificateRequest, CertificateRequestAdmin)
admin.site.register(ImageCertificateRequest, ImageCertificateRequestAdmin)
admin.site.register(CertificateShipping, ShippingCertificateAdmin)
admin.site.register(ArtistTagRequest, ArtistTagRequestAdmin)
admin.site.register(Collection, CollectionAdmin)
admin.site.register(LikeCollection, LikeCollectionAdmin)
admin.site.register(LikeArtwork, LikeArtworkAdmin)
admin.site.register(ArtworkArtist, ArtworkArtistAdmin)
admin.site.register(Exhibition, ExhibitionAdmin)
admin.site.register(ExhibitionGroup, ExhibitionGroupAdmin)
admin.site.register(ShareLink, ShareLinkAdmin)
admin.site.register(CommentArtwork, CommentArtworkAdmin)
admin.site.register(CollectorOwnershipTransfer, CollectorOwnershipTransferAdmin)

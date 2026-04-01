from django.conf import settings
from rest_framework import serializers
from rest_framework.generics import get_object_or_404
from django.utils.translation import gettext as _

from activity_log.models import ArtworkLog, CertificateLog
from activity_log.models.artwork_log import (
    ACTION_CERTIFICATE_ISSUED,
    ACTION_CERTIFICATE_REQUESTED,
    ACTION_UPDATE_ARTWORK,
)
from artwork.models import ArtWork, ArtistTagRequest, Collection, ArtworkArtist
from artwork.models import CommentArtwork
from artwork.models import StyleArtwork
from artwork.models import SubjectArtwork
from artwork.models import OrientationArtwork
from artwork.models import ImageCertificateRequest
from artwork.models import SizeArtwork
from artwork.models import ImageArtwork
from artwork.models import ConditionImageBatch, ConditionImage
from artwork.models import ConditionImageBatchLog
from artwork.models import MediumArtwork
from artwork.models import OwnerCertificate
from artwork.models import CertificateShipping
from artwork.models import ArtworkCertificate
from artwork.models import ArtworkEdition
from artwork.models import CertificateRequest
from artwork.models.certificate_request import STATUS
from artwork.utils.const import CATEGORY_CHOICES, STATUS_CHOICES
from artwork.utils.artwork import (
    copy_artwork,
    copy_artwork_edition,
)
from artwork.utils.inventory_code import generate_inventory_code
from artwork.task.notification import notify_receive_request_certificate

from common.serializers.common import ChoiceFieldSerializer
from core.accounts.api.location import UserLocationSerializer
from core.accounts.api.user_api import UserSerializer
from core.accounts.models import User
from core.accounts.models.user import USER_ROLE
from core.accounts.serializers.artist import ArtistArtWorkSerializer


class ArtworkArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArtworkArtist
        fields = ('artist_name', 'contact_info', 'year_of_birth')


class ArtistTagRequestSerializer(serializers.ModelSerializer):
    request_by = serializers.IntegerField(write_only=True)
    request_to = serializers.IntegerField(write_only=True)

    class Meta:
        model = ArtistTagRequest
        fields = ['request_by', 'request_to', 'status', 'message']


class GetArtistTagRequestSerializer(serializers.ModelSerializer):
    request_to = ArtistArtWorkSerializer()
    request_by = UserSerializer()
    status = serializers.IntegerField()

    class Meta:
        model = ArtistTagRequest
        fields = ['id', 'artwork', 'request_by', 'request_to', 'status', 'message', 'created_at']


class ArtworkEditionNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArtworkEdition
        fields = ['id', 'edition_number']


class OwnerArtWorkSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'uuid', 'name', 'role', 'avatar')


class SizeArtworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SizeArtwork
        fields = ('length', 'width', 'height', 'depth', 'weight')

    def to_representation(self, instance):
        if not isinstance(instance, SizeArtwork):
            return super().to_representation(instance)

        representation = super().to_representation(instance)
        for field in ['length', 'width', 'height', 'depth', 'weight']:
            value = getattr(instance, field)
            if value is not None:
                value = float(value)
                if value.is_integer():
                    representation[field] = int(value)
                else:
                    representation[field] = value
        return representation


class MediumSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediumArtwork
        fields = ('id', 'name', 'name_vi', 'category', 'user')


class StyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = StyleArtwork
        fields = ('id', 'name', 'name_vi', 'category', 'user')


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubjectArtwork
        fields = ('id', 'name', 'name_vi', 'category', 'user')


class OrientationSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrientationArtwork
        fields = ('id', 'name', 'name_vi', 'category')


class ArtistSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'name', 'role', 'legal_name', 'avatar', 'uuid')


class BaseArtWorkSerializer(serializers.ModelSerializer):
    is_owner = serializers.BooleanField(read_only=True)
    has_certificate = serializers.BooleanField(read_only=True)
    size = SizeArtworkSerializer(required=False)
    style = StyleSerializer(required=False, allow_null=True)
    subject = SubjectSerializer(required=False, allow_null=True)
    medium = MediumSerializer()

    class Meta:
        model = ArtWork
        fields = (
            'id',
            'uuid',
            'owner',
            'title',
            'description',
            'note',
            'category',
            'style',
            'subject',
            'medium',
            'orientation',
            'status',
            'price',
            'currency',
            'is_public',
            'is_hide_price',
            'year_created',
            'period_created',
            'total_edition',
            'location',
            'is_owner',
            'piece',
            'has_certificate',
            'size',
            'is_public_certificate',
            'is_ask_price_visible',
            'contact_information',
            'inventory_code',
        )

    def to_representation(self, instance):
        user = self.context['request'].user
        instance.is_owner = instance.has_owner(user)
        # Call via class so we do not replace the model method with a bool on reuse of the same instance.
        instance.has_certificate = type(instance).has_certificate(instance)
        return super().to_representation(instance)


class GetOwnerCertificateSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = OwnerCertificate
        fields = (
            'id',
            'user',
            'name',
            'year_of_birth',
            'address',
            'contract_number',
        )


class OwnerCertificateSerializer(serializers.ModelSerializer):
    name = serializers.CharField(required=False, allow_blank=True)
    year_of_birth = serializers.IntegerField(required=False, allow_null=True)
    address = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = OwnerCertificate
        fields = (
            'id',
            'user',
            'name',
            'year_of_birth',
            'address',
            'contract_number',
        )


class CertificateShippingSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificateShipping
        fields = (
            'recipient',
            'address',
            'phone_number',
        )


class CreateCertificateSerializer(serializers.Serializer):
    edition_id = serializers.IntegerField()
    owner_info = OwnerCertificateSerializer()
    issued_to_id = serializers.IntegerField()

    def validate_edition_id(self, edition_id):
        edition = get_object_or_404(ArtworkEdition, pk=edition_id)
        certificate = getattr(edition, 'certificate', None)
        if certificate:
            raise serializers.ValidationError(_('This artwork edition already has a certificate.'))
        return edition

    def create_certificate_logs(self, user, certificate, issued_to):
        artwork = certificate.artwork_edition.artwork

        CertificateLog.objects.create(
            user=user,
            certificate=certificate,
            data=(
                    _("A certificate for the artwork '%(title)s' was issued.")
                    % {'title': certificate.artwork_edition.artwork.title}
            ),
        )

        params_1 = {
            'field': 'certificate_issued',
            'title': artwork.title,
            'issued_to': getattr(issued_to, 'name', ''),
        }
        template_en_1 = 'Issued certificate for artwork {title} (to: {issued_to})'
        template_vi_1 = 'Đã tạo chứng nhận cho tác phẩm {title} (tới: {issued_to})'
        ArtworkLog.objects.create(
            artwork=artwork,
            user=user,
            action_type=ACTION_CERTIFICATE_ISSUED,
            content_en=template_en_1.format(**params_1),
            content_vi=template_vi_1.format(**params_1),
            template_en=template_en_1,
            template_vi=template_vi_1,
            params=params_1,
        )

        params_2 = {
            'field': 'certificate_received',
            'title': artwork.title,
            'request_by': getattr(user, 'name', ''),
        }
        template_en_2 = 'Certificate received for artwork {title} (from: {request_by}).'
        template_vi_2 = 'Đã nhận chứng nhận cho tác phẩm {title} (từ: {request_by}).'
        ArtworkLog.objects.create(
            artwork=artwork,
            user=issued_to,
            action_type=ACTION_CERTIFICATE_ISSUED,
            content_en=template_en_2.format(**params_2),
            content_vi=template_vi_2.format(**params_2),
            template_en=template_en_2,
            template_vi=template_vi_2,
            params=params_2,
        )

    def process(self):
        user = self.context['request'].user
        edition = self.validated_data['edition_id']
        issued_to = get_object_or_404(User, pk=self.validated_data['issued_to_id'])

        certificate = ArtworkCertificate.objects.create(artwork_edition=edition,
                                                        issued_by=user, issued_to=issued_to)
        OwnerCertificate.objects.create(certificate=certificate, **self.validated_data['owner_info'])

        if issued_to.id != user.id:
            sample_artwork = edition.artwork

            attribute_data = {
                'owner': issued_to,
            }

            artwork_copy = copy_artwork(sample_artwork=sample_artwork, attribute_data=attribute_data)

            edition_attribute_data = {
                'artwork_id': artwork_copy.id,
            }
            edition_copy = copy_artwork_edition(sample_edition=edition, attribute_data=edition_attribute_data)

            artwork_copy.linked_artwork = edition.artwork
            artwork_copy.status = 'available'
            artwork_copy.save()

            edition_copy.artwork = artwork_copy
            edition_copy.linked_edition = edition
            edition_copy.status = 'available'
            edition_copy.save()

        original_artwork = edition.artwork
        original_artwork.status = 'sold'
        edition.status = 'sold'
        original_artwork.save()
        edition.save()

        self.create_certificate_logs(user, certificate, issued_to)

        return certificate


class CertificateSerializer(serializers.ModelSerializer):
    edition_number = serializers.IntegerField(source='artwork_edition.edition_number')
    edition_status = serializers.CharField(source='artwork_edition.status')
    issued_by = UserSerializer()
    view_url = serializers.URLField()

    class Meta:
        model = ArtworkCertificate
        fields = ('id', 'edition_number', 'code', 'created_at', 'signature', 'edition_status', 'issued_by', 'view_url')

    def to_representation(self, instance):
        instance.view_url = f'{settings.PRIMARY_SITE_URL}/view-certificate/{instance.code}'
        return super().to_representation(instance)


class LinkedEditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArtworkEdition
        fields = ('id', 'edition_number')


class ArtworkEditionSerializer(serializers.ModelSerializer):
    id_certificate = serializers.SerializerMethodField()
    id = serializers.IntegerField(read_only=False)
    linked_edition = LinkedEditionSerializer(allow_null=True, read_only=True)

    class Meta:
        model = ArtworkEdition
        fields = (
            'id',
            'edition_number',
            'status',
            'location',
            'id_certificate',
            'linked_edition',
            'owner_name',
            'currency',
            'price',
        )
        ref_name = 'ArtworkArtworkEditionSerializer'

    def get_id_certificate(self, edition):
        certificate_code = self._get_certificate_code_safely(edition, 'certificate')
        if certificate_code:
            return certificate_code

        if hasattr(edition, 'linked_edition_related'):
            certificate_code = self._get_certificate_code_safely(edition.linked_edition_related, 'certificate')
            if certificate_code:
                return certificate_code

        if hasattr(edition, 'linked_edition'):
            certificate_code = self._get_certificate_code_safely(edition.linked_edition, 'certificate')
            if certificate_code:
                return certificate_code

        return None

    def _get_certificate_code_safely(self, obj, attr_name):
        if hasattr(obj, attr_name):
            certificate = getattr(obj, attr_name)
            return certificate.code

        return None


class ArtworkAttributesMixin:
    def get_model(self, attribute_name):
        mapping = {
            'style': StyleArtwork,
            'subject': SubjectArtwork,
            'medium': MediumArtwork,
        }
        return mapping.get(attribute_name)

    def assign_artwork_attributes(self, artwork, data, attribute_name):
        if not data:
            return

        user = self.context['request'].user
        model_class = self.get_model(attribute_name)
        instance, created = model_class.objects.get_or_create(**data)

        if created:
            instance.user = user
            instance.save()

        setattr(artwork, attribute_name, instance)
        artwork.save()


class ArtWorkCreateSerializer(BaseArtWorkSerializer, ArtworkAttributesMixin):
    images = serializers.ListField(required=True, write_only=True, child=serializers.CharField())
    edition_number = serializers.IntegerField(required=False, allow_null=True)
    collections = serializers.PrimaryKeyRelatedField(queryset=Collection.objects.all(), many=True, required=False)
    subjects = serializers.PrimaryKeyRelatedField(queryset=SubjectArtwork.objects.all(), many=True, required=False)
    artist_artwork = ArtworkArtistSerializer(required=False, allow_null=True)
    audio_file = serializers.CharField(required=False, allow_null=True)
    artist_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        source='artist',
        write_only=True,
        allow_null=True,
        required=False,
    )

    class Meta(BaseArtWorkSerializer.Meta):
        model = ArtWork
        fields = BaseArtWorkSerializer.Meta.fields + ('images', 'edition_number', 'artist_id',
                                                      'collections', 'subjects', 'artist_artwork', 'audio_file')

    def validate_total_edition(self, total_edition):
        category = self.initial_data.get('category')
        if category == 'painting' and total_edition > 1:
            raise serializers.ValidationError('For paintings, the maximum total edition is 1.')
        elif category == 'sculpture' and total_edition > 100:
            raise serializers.ValidationError('For sculptures, the maximum total edition is 100.')
        return total_edition

    def validate(self, attrs):
        owner = self.context['request'].user
        edition_number = attrs.get('edition_number', None)

        if len(attrs['images']) < 1:
            raise serializers.ValidationError({'images': _('The images list must contain at least one item.')})
        if len(attrs['images']) > 5:
            raise serializers.ValidationError({'images': _('Maximum 5 images are allowed.')})

        if owner.role == USER_ROLE.COLLECTOR and not edition_number:
            raise serializers.ValidationError({'edition_number': _('Edition number is required')})
        return attrs

    def create_size_artwork(self, category, size_data):
        size = SizeArtwork.objects.create(
            category=category,
            **size_data,
        )
        return size

    def create_image_artwork(self, artwork, images):
        image_objects = [ImageArtwork(artwork=artwork, image=image) for image in images]
        ImageArtwork.objects.bulk_create(image_objects)

    def create_edition_artwork(self, artwork, edition_number):
        ArtworkEdition.objects.create(artwork=artwork, edition_number=edition_number, status=artwork.status)

    def create_editions_artwork(self, artwork, total_edition):
        editions = [
            ArtworkEdition(
                artwork=artwork,
                edition_number=i + 1,
                location=artwork.location,
                status=artwork.status,
            ) for i in range(total_edition)
        ]
        ArtworkEdition.objects.bulk_create(editions)

    def add_to_collections(self, artwork, collections):
        for collection in collections:
            collection = get_object_or_404(Collection, id=collection.id)
            collection.artworks.add(artwork)

    def create_certificate_logs(self, user, certificate):
        CertificateLog.objects.create(
            user=user,
            certificate=certificate,
            data=(
                _("A certificate for the artwork '%(title)s' was issued.")
                % {'title': certificate.artwork_edition.artwork.title}
            ),
        )

        params = {
            'field': 'certificate',
            'title': certificate.artwork_edition.artwork.title,
            'issued_to': getattr(user, 'name', '') or getattr(user, 'username', ''),
        }
        template_en = 'Issued certificate for artwork {title} (to: {issued_to})'
        template_vi = 'Đã cấp chứng nhận cho tác phẩm {title} (cho: {issued_to})'
        ArtworkLog.objects.create(
            artwork=certificate.artwork_edition.artwork,
            user=user,
            action_type=ACTION_CERTIFICATE_ISSUED,
            content_en=template_en.format(**params),
            content_vi=template_vi.format(**params),
            template_en=template_en,
            template_vi=template_vi,
            params=params,
        )

    def create(self, validated_data):
        owner = self.context['request'].user
        size = validated_data.pop('size', None)
        images = validated_data.pop('images', None)
        style = validated_data.pop('style', None)
        subject = validated_data.pop('subject', None)
        medium = validated_data.pop('medium', None)
        category = validated_data.get('category', None)
        total_edition = validated_data.get('total_edition', None)
        edition_number = validated_data.pop('edition_number', None)
        collections = validated_data.pop('collections', [])
        subjects = validated_data.pop('subjects', [])
        artist_artwork = validated_data.pop('artist_artwork', None)
        size_object = self.create_size_artwork(category, size) if size else None

        if artist_artwork:
            artwork_artist_instance, created = ArtworkArtist.objects.get_or_create(
                artist_name=artist_artwork['artist_name'],
                year_of_birth=artist_artwork['year_of_birth'],
                create_user=owner)

            artist_artwork = artwork_artist_instance

        artwork = ArtWork.objects.create(size=size_object, artist_artwork=artist_artwork, **validated_data)

        artwork._skip_logging = True

        self.assign_artwork_attributes(artwork, style, 'style')
        self.assign_artwork_attributes(artwork, subject, 'subject')
        self.assign_artwork_attributes(artwork, medium, 'medium')

        self.create_image_artwork(artwork, images)

        if owner.role == USER_ROLE.ARTIST:
            self.create_editions_artwork(artwork, total_edition)
            owner_certificate_name = getattr(owner, 'legal_name', None)

            for edition in artwork.editions.all().order_by('edition_number'):
                certificate = ArtworkCertificate.objects.create(
                    artwork_edition=edition,
                    issued_by=owner,
                    issued_to=owner,
                )

                OwnerCertificate.objects.create(
                    certificate=certificate,
                    user=owner,
                    name=owner_certificate_name,
                )

                self.create_certificate_logs(owner, certificate)

        if owner.role != USER_ROLE.ARTIST:
            self.create_edition_artwork(artwork, edition_number)

        self.add_to_collections(artwork, collections)
        artwork.subjects.set(subjects)
        artwork.save()

        artwork.inventory_code = generate_inventory_code(artwork)
        artwork.save(update_fields=['inventory_code'])

        return artwork


class LinkedArtworkSerializer(serializers.ModelSerializer):
    artist = ArtistSerializer()

    class Meta:
        model = ArtWork
        fields = (
            'id',
            'artist',
        )
        ref_name = 'LinkedArtworkSerializerRef'


class ArtworkSerializer(BaseArtWorkSerializer):
    images = serializers.ListField(read_only=True, child=serializers.ImageField())
    key_images = serializers.ListField(read_only=True, child=serializers.CharField())
    category = ChoiceFieldSerializer(choices=CATEGORY_CHOICES)
    status = ChoiceFieldSerializer(choices=STATUS_CHOICES)
    certificate = CertificateSerializer(allow_null=True)
    location = UserLocationSerializer()
    orientation = OrientationSerializer(required=False)
    editions = serializers.SerializerMethodField()
    owner = OwnerArtWorkSerializer()
    number_of_likes = serializers.IntegerField(read_only=True)
    is_user_like = serializers.BooleanField(read_only=True)
    artist_artwork = ArtworkArtistSerializer()
    audio_file = serializers.ImageField(read_only=True)
    comments = serializers.SerializerMethodField()
    condition_images = serializers.SerializerMethodField()
    key_condition_images = serializers.ListField(read_only=True, child=serializers.CharField())
    artist = ArtistSerializer()
    linked_artwork = LinkedArtworkSerializer()
    can_sync_certificates = serializers.BooleanField(read_only=True)

    class Meta:
        model = ArtWork
        fields = BaseArtWorkSerializer.Meta.fields + ('images', 'certificate', 'key_images', 'editions',
                                                      'number_of_likes',
                                                      'is_user_like', 'subjects', 'artist_artwork', 'audio_file',
                                                      'comments', 'condition_images', 'in_stock_date',
                                                      'key_condition_images', 'artist', 'linked_artwork',
                                                      'show_comments', 'can_sync_certificates')

    def get_editions(self, obj):
        editions = obj.editions.all().order_by('edition_number')
        return ArtworkEditionSerializer(editions, many=True, read_only=True).data

    def get_certificate(self, instance):
        if getattr(instance, 'certificate', None):
            return

        edition = instance.editions.all().order_by('edition_number', 'id').first()
        certificate = None
        if edition:
            certificate = ArtworkCertificate.objects.filter(
                artwork_edition=edition,
            ).order_by('id').first()

        if certificate:
            instance.certificate = certificate
            return

        linked_certificate = None

        linked_edition = getattr(edition, 'linked_edition', None)
        if linked_edition:
            linked_certificate = ArtworkCertificate.objects.filter(
                artwork_edition=linked_edition,
            ).order_by('id').first()
            instance.certificate = linked_certificate
            return

        linked_artworks = instance.linked_artworks.filter(editions__certificate__isnull=False).first()
        if linked_artworks:
            linked_certificate = ArtworkCertificate.objects.filter(
                artwork_edition__artwork=linked_artworks,
            ).order_by('id').first()

        instance.certificate = linked_certificate

    def get_comments(self, obj):
        qs = obj.comments.all().order_by('created_at')
        return CommentArtworkSerializer(qs, many=True, context=self.context).data

    def get_condition_images(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)

        if not user or user.is_anonymous:
            return []

        qs = ConditionImage.objects.filter(
            batch__artwork=obj,
            batch__owner=user,
        ).order_by('order', 'id')

        serialized = ConditionImageSerializer(qs, many=True, read_only=True, context=self.context).data
        return [item.get('image') for item in serialized]

    def to_representation(self, instance):
        user = self.context['request'].user

        images = ImageArtwork.objects.filter(artwork=instance)
        instance.images = [item.image if item.image else None for item in images]
        instance.key_images = [item.image if item.image else None for item in images]

        if not user.is_anonymous:
            cond_images = (ConditionImage.objects.filter(batch__artwork=instance, batch__owner=user).
                           order_by('order', 'id'))
            instance.key_condition_images = [
                (item.image.name if getattr(item, 'image', None) else None)
                for item in cond_images
            ]
        else:
            instance.key_condition_images = []

        if not user.is_anonymous:
            instance.is_user_like = instance.like_artworks.filter(user=user).exists()
        else:
            instance.is_user_like = False

        instance.number_of_likes = instance.like_artworks.count()

        self.get_certificate(instance)

        instance.can_sync_certificates = instance.can_sync_certificates()

        return super().to_representation(instance)


class ConditionImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConditionImage
        fields = ('image', 'order')


class ArtworkEditionCustomSerializer(ArtworkEditionSerializer):
    id = serializers.IntegerField(read_only=False)


class CommentVisibilityUpdateSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    is_hidden = serializers.BooleanField(required=False, allow_null=True)


class CommentUpdateSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False, allow_null=True)
    content = serializers.CharField(required=False, allow_blank=True)
    visibility_updates = CommentVisibilityUpdateSerializer(many=True, required=False)


def _process_comment_updates(instance, user, comment):
    if comment is None:
        return
    c_id = comment.get('id') if isinstance(comment, dict) else None
    c_content = comment.get('content') if isinstance(comment, dict) else None
    visibility_updates = comment.get('visibility_updates') if isinstance(comment, dict) else None

    if c_content is not None:
        if c_id:
            c_obj = get_object_or_404(CommentArtwork, pk=c_id, artwork=instance, user=user)
            c_obj.content = c_content
            c_obj.save()
        else:
            CommentArtwork.objects.create(artwork=instance, user=user, content=c_content)

    if visibility_updates:
        for item in visibility_updates:
            cid = item.get('id')
            hidden = item.get('is_hidden')
            if cid is None or hidden is None:
                continue
            c_obj = get_object_or_404(CommentArtwork, pk=cid, artwork=instance)
            if c_obj.is_hidden != bool(hidden):
                c_obj.is_hidden = bool(hidden)
                c_obj.save(update_fields=['is_hidden'])


class CommentArtworkSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = CommentArtwork
        fields = ('id', 'user', 'content', 'created_at', 'is_hidden')


class ArtWorkUpdateFullFieldSerializer(BaseArtWorkSerializer, ArtworkAttributesMixin):
    images = serializers.ListField(write_only=True, child=serializers.CharField(), required=False)
    total_edition = serializers.IntegerField(read_only=True)
    edition = ArtworkEditionCustomSerializer(required=False, allow_null=True)
    artist_artwork = ArtworkArtistSerializer(required=False, allow_null=True)
    audio_file = serializers.CharField(required=False, allow_null=True)
    comment = CommentUpdateSerializer(required=False, allow_null=True, write_only=True)
    artist_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(role=USER_ROLE.ARTIST),
        source='artist',
        write_only=True,
        allow_null=True,
        required=False,
    )

    class Meta(BaseArtWorkSerializer.Meta):
        model = ArtWork
        fields = BaseArtWorkSerializer.Meta.fields + (
            'images', 'edition', 'subjects', 'artist_artwork',
            'audio_file', 'comment', 'artist_id', 'show_comments',
        )

    def validate(self, data):
        data = super().validate(data)

        if 'images' in data:
            images_length = len(data['images'])
            if images_length < 1:
                raise serializers.ValidationError('The images list must contain at least one item.')
            if images_length > 5:
                raise serializers.ValidationError('The images list must not contain more than five items.')

        return data

    def update_size_artwork(self, artwork, size_data):
        from activity_log.models import ArtworkLog

        if artwork.size:
            old_size_str = self._get_size_display(artwork.size)

            for attr, value in size_data.items():
                setattr(artwork.size, attr, value)
            artwork.size.save()

            new_size_str = self._get_size_display(artwork.size)

            if old_size_str != new_size_str:
                inventory_code = artwork.inventory_code or 'N/A'
                art_title = getattr(artwork, 'title', None) or f"Artwork #{getattr(artwork, 'pk', '?')}"
                user = getattr(artwork, '_current_user', None)

                params = {
                    'field': 'size',
                    'old': old_size_str,
                    'new': new_size_str,
                    'title': art_title,
                    'inventory_code': inventory_code,
                }
                template_en = (
                    'Changed {field} of artwork {title} (inventory code: {inventory_code}) '
                    'from {old} to {new}'
                )
                template_vi = (
                    'Đã thay đổi {field} của tác phẩm {title} (mã kiểm kê: {inventory_code}) '
                    'từ {old} thành {new}'
                )

                ArtworkLog.objects.create(
                    artwork=artwork,
                    user=user,
                    action_type=ACTION_UPDATE_ARTWORK,
                    content_en=template_en.format(**params),
                    content_vi=template_vi.format(**params),
                    template_en=template_en,
                    template_vi=template_vi,
                    params=params,
                )
        else:
            category = artwork.category
            size = SizeArtwork.objects.create(category=category, **size_data)
            artwork.size = size
            artwork.save()

            new_size_str = self._get_size_display(size)
            inventory_code = artwork.inventory_code or 'N/A'
            art_title = getattr(artwork, 'title', None) or f"Artwork #{getattr(artwork, 'pk', '?')}"
            user = getattr(artwork, '_current_user', None)

            params = {
                'field': 'size',
                'old': 'N/A',
                'new': new_size_str,
                'title': art_title,
                'inventory_code': inventory_code,
            }
            template_en = 'Changed {field} of artwork {title} (inventory code: {inventory_code}) from {old} to {new}'
            template_vi = 'Đã thay đổi {field} của tác phẩm {title} (mã kiểm kê: {inventory_code}) từ {old} thành {new}'

            ArtworkLog.objects.create(
                artwork=artwork,
                user=user,
                action_type=ACTION_UPDATE_ARTWORK,
                content_en=template_en.format(**params),
                content_vi=template_vi.format(**params),
                template_en=template_en,
                template_vi=template_vi,
                params=params,
            )

    def _get_size_display(self, size):
        """Helper to get human-readable size display"""
        if not size:
            return 'N/A'

        parts = []
        if hasattr(size, 'width') and size.width:
            parts.append(f'W:{size.width}')
        if hasattr(size, 'height') and size.height:
            parts.append(f'H:{size.height}')
        if hasattr(size, 'depth') and size.depth:
            parts.append(f'D:{size.depth}')
        if hasattr(size, 'unit') and size.unit:
            return f"{' x '.join(parts)} {size.unit}" if parts else 'N/A'

        return ' x '.join(parts) if parts else 'N/A'

    def update_image_artwork(self, instance, images):
        user = self.context['request'].user
        existing_images = ImageArtwork.objects.filter(artwork=instance)
        existing_filenames = [image.image for image in existing_images]

        for image in images:
            if image not in existing_filenames:
                image_obj = ImageArtwork(artwork=instance, image=image)
                image_obj._current_user = user
                image_obj.save()

        images_to_delete = ImageArtwork.objects.filter(
            artwork=instance, image__in=existing_filenames,
        ).exclude(image__in=images)

        for img in images_to_delete:
            img._current_user = user
            img.delete()

    def update_edition(self, instance, edition):
        ArtworkEdition.objects.update_or_create(
            artwork=instance,
            pk=edition.get('id', None),
            defaults={
                'edition_number': edition['edition_number'],
                'status': instance.status,
                'artwork': instance,
            },
        )

    def update(self, instance, validated_data):
        user = self.context['request'].user
        collector_transfer_payload = None
        if getattr(user, 'role', None) == USER_ROLE.COLLECTOR and 'owner' in validated_data:
            new_owner = validated_data.get('owner')
            if instance.owner_id == user.id and new_owner and getattr(new_owner, 'id', None) != user.id:
                from artwork.utils.collector_transfer_snapshot import build_collector_transfer_snapshot

                collector_transfer_payload = {
                    'snapshot': build_collector_transfer_snapshot(instance, self.context['request']),
                    'transferee': new_owner,
                }

        size_data = validated_data.pop('size', None)
        images = validated_data.pop('images', None)
        style = validated_data.pop('style', None)
        subject = validated_data.pop('subject', None)
        medium = validated_data.pop('medium', None)
        edition = validated_data.pop('edition', None)
        subjects = validated_data.pop('subjects', [])
        comment = validated_data.pop('comment', None)

        if 'artist' in validated_data:
            instance.artist = validated_data.pop('artist', None)
            instance.artist_artwork = None

        if 'artist_artwork' in validated_data:
            artist_artwork_data = validated_data.pop('artist_artwork', None)
            if artist_artwork_data:
                artwork_artist_instance, _ = ArtworkArtist.objects.get_or_create(
                    artist_name=artist_artwork_data['artist_name'],
                    year_of_birth=artist_artwork_data['year_of_birth'],
                    create_user=user,
                )
                instance.artist_artwork = artwork_artist_instance
                instance.artist = None
            else:
                instance.artist_artwork = None

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.subjects.set(subjects)
        instance.save()

        self.assign_artwork_attributes(instance, style, 'style')
        self.assign_artwork_attributes(instance, subject, 'subject')
        self.assign_artwork_attributes(instance, medium, 'medium')

        if size_data:
            self.update_size_artwork(instance, size_data)
        if images:
            self.update_image_artwork(instance, images)
        if edition:
            self.update_edition(instance, edition)

        _process_comment_updates(instance, user, comment)

        if collector_transfer_payload:
            from artwork.models import CollectorOwnershipTransfer

            CollectorOwnershipTransfer.objects.create(
                transferrer=user,
                transferee=collector_transfer_payload['transferee'],
                artwork=instance,
                certificate=None,
                snapshot=collector_transfer_payload['snapshot'],
            )

        return instance


class ArtWorkUpdateLessFieldSerializer(serializers.ModelSerializer):
    audio_file = serializers.CharField(required=False, allow_null=True)
    condition_images = serializers.ListField(write_only=True, child=serializers.CharField(), required=False)
    comment = CommentUpdateSerializer(required=False, allow_null=True, write_only=True)

    class Meta:
        model = ArtWork
        fields = (
            'id',
            'description',
            'note',
            'is_public',
            'is_public_certificate',
            'show_comments',
            'price',
            'is_hide_price',
            'is_ask_price_visible',
            'contact_information',
            'audio_file',
            'condition_images',
            'comment',
            'inventory_code',
            'subjects',
        )

    def update(self, instance, validated_data):
        user = self.context['request'].user
        condition_images = validated_data.pop('condition_images', None)
        comment = validated_data.pop('comment', None)
        subjects = validated_data.pop('subjects', [])

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.subjects.set(subjects)
        instance.save()

        if condition_images:
            batch, created = ConditionImageBatch.objects.get_or_create(
                artwork=instance,
                owner=user,
                defaults={'artwork': instance, 'owner': user},
            )

            existing_images = ConditionImage.objects.filter(batch=batch).order_by('order', 'id')
            existing_filenames = [img.image.name if hasattr(img.image, 'name')
                                  else str(img.image) for img in existing_images]
            incoming_list = list(condition_images)

            has_changes = existing_filenames != incoming_list

            if has_changes and not created and getattr(batch, 'update_count', 0) >= 2:
                raise serializers.ValidationError({'condition_images':
                                                   _('You can only update condition images up to 2 times.')})

            if has_changes:
                new_images_to_add = []
                for idx, image in enumerate(incoming_list):
                    if image not in existing_filenames:
                        new_images_to_add.append(ConditionImage(batch=batch, image=image, order=idx))

                if new_images_to_add:
                    ConditionImage.objects.bulk_create(new_images_to_add)

                images_to_delete = ConditionImage.objects.filter(batch=batch).exclude(
                    image__in=incoming_list,
                )
                if images_to_delete.exists():
                    images_to_delete.delete()

                order_map = {str(name): idx for idx, name in enumerate(incoming_list)}
                to_update = []
                remaining = ConditionImage.objects.filter(batch=batch, image__in=incoming_list)
                for img in remaining:
                    fname = img.image.name if hasattr(img.image, 'name') else str(img.image)
                    new_idx = order_map.get(str(fname))
                    if new_idx is not None and img.order != new_idx:
                        img.order = new_idx
                        to_update.append(img)
                if to_update:
                    ConditionImage.objects.bulk_update(to_update, ['order'])

                batch.update_count = getattr(batch, 'update_count', 0) + 1
                batch.save(update_fields=['update_count'])

                final_images_qs = ConditionImage.objects.filter(batch=batch).order_by('order', 'id')
                snapshot = [
                    (img.image.name if hasattr(img.image, 'name') else str(img.image))
                    for img in final_images_qs
                ]
                ConditionImageBatchLog.objects.create(
                    batch=batch,
                    artwork=instance,
                    actor=user,
                    images_snapshot=snapshot,
                    update_count=batch.update_count,
                )

        _process_comment_updates(instance, user, comment)

        request = self.context.get('request')
        if request and getattr(request.user, 'role', None) == USER_ROLE.ARTIST and 'description' in validated_data:
            new_description = validated_data['description']

            for linked in instance.linked_artworks.all():
                linked.description = new_description
                linked.save()

        return instance


class ArtworkInStockUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = ArtWork
        fields = (
            'status',
            'inventory_code',
            'location',
            'is_public_certificate',
        )

    def validate(self, attrs):
        from rest_framework.exceptions import PermissionDenied

        attrs = super().validate(attrs)
        user = self.context['request'].user
        artwork = self.instance

        if not artwork.has_owner(user):
            raise PermissionDenied('You do not have permission to edit this artwork.')

        if artwork.status != 'in_stock':
            raise serializers.ValidationError(_('Artwork must be in stock to update.'))

        return attrs

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if 'status' in validated_data:
            ArtworkEdition.objects.filter(artwork=instance).update(status=instance.status)

        return instance


class CollectorArtWorkUpdateSerializer(serializers.ModelSerializer):
    uuid = serializers.UUIDField()
    size = SizeArtworkSerializer()
    medium = MediumSerializer()

    class Meta:
        model = ArtWork
        fields = (
            'uuid',
            'title',
            'size',
            'medium',
            'year_created',
            'period_created',
            'total_edition',
        )


class CollectorArtWorkUpdateSerializerData(ArtWorkUpdateFullFieldSerializer):
    total_edition = serializers.IntegerField(read_only=False)


class CollectorRequestCertificateSerializer(serializers.Serializer):
    artwork = CollectorArtWorkUpdateSerializer()
    owner_info = OwnerCertificateSerializer()
    request_to = serializers.IntegerField()
    images = serializers.ListField(required=True, write_only=True, child=serializers.CharField())
    edition = ArtworkEditionSerializer()

    def validate_artwork(self, artwork):
        if self.is_certificate_requested(artwork['uuid']):
            raise serializers.ValidationError(_('This artwork already requested a certificate'))

        if not ArtworkEdition.objects.filter(artwork__uuid=artwork['uuid']).exists():
            raise serializers.ValidationError(_('Artwork should have at least one edition to request certificate'))

        return artwork

    def validate(self, attrs):
        super().validate(attrs)

        if len(attrs['images']) > 5:
            raise serializers.ValidationError({'images': _('Maximum 5 images are allowed.')})
        return attrs

    def is_certificate_requested(self, artwork_uuid):
        return ArtworkEdition.objects.filter(
            artwork__uuid=artwork_uuid,
            certificate_requests__isnull=False,
        ).exists()

    def create_certificate_request_record(self, edition):
        return CertificateRequest.objects.create(
            artwork_edition=edition,
            status=STATUS.REQUEST_RECEIVED,
            request_by=self.context['request'].user,
            request_to_id=self.validated_data['request_to'],
            owner_info=self.validated_data['owner_info'],
        )

    def create_certificate_request(self, edition):
        return self.create_certificate_request_record(edition)

    def create_image_certificate_request(self, certificate_request, images):
        image_objects = [ImageCertificateRequest(certificate_request=certificate_request, image=image)
                         for image in images]
        ImageCertificateRequest.objects.bulk_create(image_objects)

    def process(self, edition):
        images = self.validated_data['images']
        certificate_request = self.create_certificate_request(edition)
        artwork = edition.artwork
        request_by = self.context['request'].user
        request_to = get_object_or_404(User, pk=self.validated_data['request_to'])

        params_req1 = {
            'field': 'certificate_request',
            'title': artwork.title,
            'artist': request_to.name,
        }
        template_en_req1 = 'Requested certificate for artwork {title} (to artist: {artist})'
        template_vi_req1 = 'Đã yêu cầu chứng nhận cho tác phẩm {title} (tới nghệ sĩ: {artist})'
        ArtworkLog.objects.create(
            artwork=artwork,
            user=request_by,
            action_type=ACTION_CERTIFICATE_REQUESTED,
            content_en=template_en_req1.format(**params_req1),
            content_vi=template_vi_req1.format(**params_req1),
            template_en=template_en_req1,
            template_vi=template_vi_req1,
            params=params_req1,
        )

        params_req2 = {
            'field': 'certificate_request',
            'title': artwork.title,
            'request_by': request_by.name,
        }
        template_en_req2 = 'Certificate request received for artwork {title} (from: {request_by}).'
        template_vi_req2 = 'Đã nhận yêu cầu chứng nhận cho tác phẩm {title} (từ: {request_by}).'
        ArtworkLog.objects.create(
            artwork=artwork,
            user=request_to,
            action_type=ACTION_CERTIFICATE_REQUESTED,
            content_en=template_en_req2.format(**params_req2),
            content_vi=template_vi_req2.format(**params_req2),
            template_en=template_en_req2,
            template_vi=template_vi_req2,
            params=params_req2,
        )
        self.create_image_certificate_request(certificate_request, images)

        notify_receive_request_certificate.delay(receive_user_id=self.validated_data['request_to'],
                                                 request_user_id=self.context['request'].user.id,
                                                 artwork_id=edition.artwork.id,
                                                 certificate_request_id=certificate_request.id,
                                                 )
        return certificate_request


class OwnerViewInfoArtworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'role', 'name', 'uuid']


class GetArtistTagRequestViewInfoSerializer(serializers.ModelSerializer):
    request_to = ArtistArtWorkSerializer()
    status = serializers.IntegerField()

    class Meta:
        model = ArtistTagRequest
        fields = ['id', 'artwork', 'request_to', 'status', 'message', 'created_at']


class ArtworkViewInfoSerializer(BaseArtWorkSerializer):
    images = serializers.ListField(read_only=True, child=serializers.ImageField())
    key_images = serializers.ListField(read_only=True, child=serializers.CharField())
    category = ChoiceFieldSerializer(choices=CATEGORY_CHOICES)
    status = ChoiceFieldSerializer(choices=STATUS_CHOICES)
    certificate = CertificateSerializer(allow_null=True)
    location = UserLocationSerializer()
    orientation = OrientationSerializer(required=False)
    editions = serializers.SerializerMethodField()
    owner = OwnerViewInfoArtworkSerializer()
    number_of_likes = serializers.IntegerField(read_only=True)
    is_user_like = serializers.BooleanField(read_only=True)
    artist_artwork = ArtworkArtistSerializer()

    class Meta:
        model = ArtWork
        fields = BaseArtWorkSerializer.Meta.fields + ('images', 'certificate', 'key_images', 'editions',
                                                      'number_of_likes', 'is_user_like',
                                                      'artist_artwork')

    def get_editions(self, obj):
        editions = obj.editions.all().order_by('edition_number')
        return ArtworkEditionSerializer(editions, many=True, read_only=True).data

    def to_representation(self, instance):
        user = self.context['request'].user

        images = ImageArtwork.objects.filter(artwork=instance)
        instance.images = [item.image if item.image else None for item in images]
        instance.key_images = [item.image if item.image else None for item in images]

        if not user.is_anonymous:
            instance.is_user_like = instance.like_artworks.filter(user=user).exists()
        else:
            instance.is_user_like = False

        instance.number_of_likes = instance.like_artworks.count()
        return super().to_representation(instance)

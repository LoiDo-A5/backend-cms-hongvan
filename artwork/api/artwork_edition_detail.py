from rest_framework.generics import UpdateAPIView
from rest_framework.permissions import IsAuthenticated

from activity_log.models.artwork_log import ACTION_UPDATE_ARTWORK
from activity_log.models import ArtworkLog
from artwork.models.artwork_edition import ArtworkEdition
from artwork.serializers.artwork_edition import EditionSerializer
from django.db import transaction


class ArtworkEditionDetailApi(UpdateAPIView):
    serializer_class = EditionSerializer
    permission_classes = (IsAuthenticated,)
    queryset = ArtworkEdition.objects.all()

    def update(self, request, *args, **kwargs):
        with transaction.atomic():
            edition_before = self.get_object()
            old_values = {
                'owner_name': edition_before.owner_name,
                'currency': edition_before.currency,
                'price': str(edition_before.price) if edition_before.price is not None else None,
            }
            response = super().update(request, *args, **kwargs)
            if response.status_code == 200:
                edition_instance = self.get_object()
                artwork = edition_instance.artwork

                new_values = {
                    'owner_name': edition_instance.owner_name,
                    'currency': edition_instance.currency,
                    'price': str(edition_instance.price) if edition_instance.price is not None else None,
                }

                template_en = (
                    'Changed {field} of artwork {title} (inventory code: {inventory_code}) '
                    'from {old} to {new}'
                )
                template_vi = (
                    'Đã thay đổi {field} của tác phẩm {title} (mã kiểm kê: {inventory_code}) '
                    'từ {old} thành {new}'
                )
                inventory_code = artwork.inventory_code or 'N/A'
                title = getattr(artwork, 'title', None) or f"Artwork #{getattr(artwork, 'pk', '?')}"

                field_labels = {
                    'owner_name': f'edition {edition_instance.edition_number} owner name',
                    'currency': f'edition {edition_instance.edition_number} currency',
                    'price': f'edition {edition_instance.edition_number} price',
                }

                for field_name, field_label in field_labels.items():
                    old = old_values.get(field_name)
                    new = new_values.get(field_name)
                    if old != new:
                        params = {
                            'field': field_label,
                            'title': title,
                            'inventory_code': inventory_code,
                            'old': old,
                            'new': new,
                        }
                        ArtworkLog.objects.create(
                            artwork=artwork,
                            user=request.user,
                            action_type=ACTION_UPDATE_ARTWORK,
                            content_en=template_en.format(**params),
                            content_vi=template_vi.format(**params),
                            template_en=template_en,
                            template_vi=template_vi,
                            params=params,
                        )

                edition_statuses = [edition.status for edition in artwork.editions.all()]

                if any(status in ['available', 'consignment'] for status in edition_statuses):
                    artwork.status = 'available'
                elif any(status == 'sold' for status in edition_statuses) and not any(
                        status in ['available', 'consignment'] for status in edition_statuses):
                    artwork.status = 'sold'
                elif not any(
                        edition_status in ['available', 'consignment', 'sold', 'donated_gifted'] for edition_status in
                        edition_statuses):
                    artwork.status = 'not_for_sale'
                else:
                    artwork.status = edition_statuses[0] if edition_statuses else artwork.status

                artwork._current_user = request.user
                artwork.save()

            return response

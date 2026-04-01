from django.db.models.signals import post_save, post_delete, pre_save, pre_delete, m2m_changed
from django.dispatch import receiver

from activity_log.models import ArtworkLog
from activity_log.models.artwork_log import (
    ACTION_UPDATE_ARTWORK,
    ACTION_CERTIFICATE_ISSUED,
    ACTION_ARTWORK_UPLOADED,
)
from artwork.models import ArtWork, ImageArtwork, ArtworkCertificate, ExhibitionGroup
from artwork.models.artwork import CURRENCY_CHOICES
from artwork.utils.const import STATUS_CHOICES


def get_status_display(status_value):
    for choice_value, choice_display in STATUS_CHOICES:
        if choice_value == status_value:
            return choice_display
    return status_value


def get_currency_display(currency_value):
    for choice_value, choice_display in CURRENCY_CHOICES:
        if choice_value == currency_value:
            return choice_display
    return currency_value


def get_location_display(location):
    if location:
        return getattr(location, 'name', str(location))
    return 'N/A'


def get_related_object_display(obj):
    if obj is None:
        return 'N/A'
    return getattr(obj, 'name', str(obj))


def create_artwork_log(
    artwork,
    action_type,
    content_en=' ',
    content_vi=' ',
    template_en=' ',
    template_vi=' ',
    params=None,
    user=None,
):
    if not artwork:
        return
    if getattr(artwork, '_skip_logging', False):
        return
    try:
        if isinstance(artwork, ArtWork):
            if artwork.pk in _DELETING_ARTWORK_IDS:
                return
            if not ArtWork.objects.filter(pk=artwork.pk).exists():
                return
    except Exception:
        return

    if user is None and hasattr(artwork, '_current_user'):
        user = artwork._current_user

    try:
        fmt_params = params or {}
        ArtworkLog.objects.create(
            artwork=artwork,
            user=user,
            action_type=action_type,
            content_en=(
                (content_en or template_en or '').format(**fmt_params)
                if fmt_params else (content_en or template_en or '')
            ),
            content_vi=(
                (content_vi or template_vi or '').format(**fmt_params)
                if fmt_params else (content_vi or template_vi or '')
            ),
            template_en=template_en or '',
            template_vi=template_vi or '',
            params=fmt_params,
        )
    except Exception:
        # Swallow logging errors to never block business ops
        import logging
        logging.getLogger(__name__).warning('Failed to create artwork log', exc_info=True)
        return


def track_field_change(old_instance, new_instance, field_name, action_type, display_name):
    old_value = getattr(old_instance, field_name, None)
    new_value = getattr(new_instance, field_name, None)

    # Build robust title once
    art_title = getattr(new_instance, 'title', None) or f"Artwork #{getattr(new_instance, 'pk', '?')}"

    if field_name == 'status':
        if old_value != new_value:
            old_display = get_status_display(old_value) if old_value else 'N/A'
            new_display = get_status_display(new_value) if new_value else 'N/A'
            inventory_code = new_instance.inventory_code or 'N/A'
            params = {
                'field': display_name,
                'title': art_title,
                'inventory_code': inventory_code,
                'old': old_display,
                'new': new_display,
            }
            template_en = 'Changed {field} of artwork {title} (inventory code: {inventory_code}) from {old} to {new}'
            template_vi = 'Đã thay đổi {field} của tác phẩm {title} (mã kiểm kê: {inventory_code}) từ {old} thành {new}'
            ArtworkLog.objects.create(
                artwork=new_instance,
                user=getattr(new_instance, '_current_user', None),
                action_type=ACTION_UPDATE_ARTWORK,
                content_en=template_en.format(**params),
                content_vi=template_vi.format(**params),
                template_en=template_en,
                template_vi=template_vi,
                params=params,
            )
    elif field_name == 'currency':
        if old_value != new_value:
            old_display = get_currency_display(old_value) if old_value else 'N/A'
            new_display = get_currency_display(new_value) if new_value else 'N/A'
            inventory_code = new_instance.inventory_code or 'N/A'
            params = {
                'field': display_name,
                'title': art_title,
                'inventory_code': inventory_code,
                'old': old_display,
                'new': new_display,
            }
            template_en = 'Changed {field} of artwork {title} (inventory code: {inventory_code}) from {old} to {new}'
            template_vi = 'Đã thay đổi {field} của tác phẩm {title} (mã kiểm kê: {inventory_code}) từ {old} thành {new}'
            ArtworkLog.objects.create(
                artwork=new_instance,
                user=getattr(new_instance, '_current_user', None),
                action_type=action_type,
                content_en=template_en.format(**params),
                content_vi=template_vi.format(**params),
                template_en=template_en,
                template_vi=template_vi,
                params=params,
            )
    elif field_name == 'is_public_certificate':
        if old_value != new_value:
            old_display = 'Public' if old_value else 'Private'
            new_display = 'Public' if new_value else 'Private'
            inventory_code = new_instance.inventory_code or 'N/A'
            params = {
                'title': art_title,
                'inventory_code': inventory_code,
                'old': old_display,
                'new': new_display,
            }
            template_en = (
                "Changed certificate visibility of artwork '{title}' (inventory code: {inventory_code}) "
                "from '{old}' to '{new}'"
            )
            template_vi = (
                "Đã thay đổi hiển thị chứng nhận của tác phẩm '{title}' (mã kiểm kê: {inventory_code}) "
                "từ '{old}' thành '{new}'"
            )
            ArtworkLog.objects.create(
                artwork=new_instance,
                user=getattr(new_instance, '_current_user', None),
                action_type=action_type,
                content_en=template_en.format(**params),
                content_vi=template_vi.format(**params),
                template_en=template_en,
                template_vi=template_vi,
                params=params,
            )
    elif field_name == 'location_id':
        if old_value != new_value:
            old_location = old_instance.location if hasattr(old_instance, 'location') else None
            new_location = new_instance.location if hasattr(new_instance, 'location') else None
            old_display = get_location_display(old_location)
            new_display = get_location_display(new_location)
            inventory_code = new_instance.inventory_code or 'N/A'
            params = {
                'field': display_name,
                'title': art_title,
                'inventory_code': inventory_code,
                'old': old_display,
                'new': new_display,
            }
            template_en = 'Changed {field} of artwork {title} (inventory code: {inventory_code}) from {old} to {new}'
            template_vi = 'Đã thay đổi {field} của tác phẩm {title} (mã kiểm kê: {inventory_code}) từ {old} thành {new}'
            create_artwork_log(
                artwork=new_instance,
                action_type=action_type,
                content_en=template_en,
                content_vi=template_vi,
                template_en=template_en,
                template_vi=template_vi,
                params=params,
                user=getattr(new_instance, '_current_user', None),
            )
    elif field_name in ['style_id', 'medium_id', 'orientation_id']:
        if old_value != new_value:
            field_attr = field_name.replace('_id', '')
            old_obj = getattr(old_instance, field_attr, None) if hasattr(old_instance, field_attr) else None
            new_obj = getattr(new_instance, field_attr, None) if hasattr(new_instance, field_attr) else None
            old_display = get_related_object_display(old_obj)
            new_display = get_related_object_display(new_obj)
            inventory_code = new_instance.inventory_code or 'N/A'
            params = {
                'field': display_name,
                'title': art_title,
                'inventory_code': inventory_code,
                'old': old_display,
                'new': new_display,
            }
            template_en = 'Changed {field} of artwork {title} (inventory code: {inventory_code}) from {old} to {new}'
            template_vi = 'Đã thay đổi {field} của tác phẩm {title} (mã kiểm kê: {inventory_code}) từ {old} thành {new}'
            create_artwork_log(
                artwork=new_instance,
                action_type=action_type,
                content_en=template_en,
                content_vi=template_vi,
                template_en=template_en,
                template_vi=template_vi,
                params=params,
                user=getattr(new_instance, '_current_user', None),
            )
    else:
        if old_value != new_value:
            inventory_code = new_instance.inventory_code or 'N/A'
            old_display = str(old_value) if old_value else 'N/A'
            new_display = str(new_value) if new_value else 'N/A'
            params = {
                'field': display_name,
                'title': art_title,
                'inventory_code': inventory_code,
                'old': old_display,
                'new': new_display,
            }
            template_en = 'Changed {field} of artwork {title} (inventory code: {inventory_code}) from {old} to {new}'
            template_vi = 'Đã thay đổi {field} của tác phẩm {title} (mã kiểm kê: {inventory_code}) từ {old} thành {new}'
            create_artwork_log(
                artwork=new_instance,
                action_type=action_type,
                content_en=template_en,
                content_vi=template_vi,
                template_en=template_en,
                template_vi=template_vi,
                params=params,
                user=getattr(new_instance, '_current_user', None),
            )


_DELETING_ARTWORK_IDS = set()


@receiver(pre_delete, sender=ArtWork)
def _mark_artwork_deleting(sender, instance, **kwargs):
    if instance and instance.pk:
        _DELETING_ARTWORK_IDS.add(instance.pk)


@receiver(post_delete, sender=ArtWork)
def _unmark_artwork_deleting(sender, instance, **kwargs):
    if instance and instance.pk and instance.pk in _DELETING_ARTWORK_IDS:
        _DELETING_ARTWORK_IDS.discard(instance.pk)


@receiver(pre_delete, sender=ArtWork)
def track_artwork_deleted(sender, instance, **kwargs):
    user = getattr(instance, '_current_user', None)
    inventory_code = getattr(instance, 'inventory_code', None) or 'N/A'
    art_title = getattr(instance, 'title', None) or f"Artwork #{getattr(instance, 'pk', '?')}"
    template_en = "Deleted artwork '{title}' (inventory code: {inventory_code})"
    template_vi = "Đã xoá tác phẩm '{title}' (mã kiểm kê: {inventory_code})"
    snapshot = {
        'id': getattr(instance, 'pk', None),
        'title': getattr(instance, 'title', None),
        'inventory_code': getattr(instance, 'inventory_code', None),
        'owner_id': getattr(instance, 'owner_id', None),
    }
    try:
        params = {
            'title': art_title,
            'inventory_code': inventory_code,
            'snapshot': snapshot,
            'event': 'delete_artwork',
        }
        ArtworkLog.objects.create(
            artwork=None,
            user=user,
            action_type=ACTION_UPDATE_ARTWORK,
            content_en=template_en.format(**params),
            content_vi=template_vi.format(**params),
            template_en=template_en,
            template_vi=template_vi,
            params=params,
        )
    except Exception:
        import logging
        logging.getLogger(__name__).warning('Failed to record artwork deletion log', exc_info=True)


@receiver(pre_save, sender=ArtWork)
def track_artwork_changes(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_instance = ArtWork.objects.get(pk=instance.pk)

            track_field_change(old_instance, instance, 'title', ACTION_UPDATE_ARTWORK, 'title')
            track_field_change(old_instance, instance, 'description', ACTION_UPDATE_ARTWORK, 'description')
            track_field_change(old_instance, instance, 'note', ACTION_UPDATE_ARTWORK, 'note')
            track_field_change(old_instance, instance, 'inventory_code', ACTION_UPDATE_ARTWORK, 'inventory code')
            track_field_change(old_instance, instance, 'status', ACTION_UPDATE_ARTWORK, 'status')
            track_field_change(old_instance, instance, 'location_id', ACTION_UPDATE_ARTWORK, 'location')
            track_field_change(old_instance, instance, 'year_created', ACTION_UPDATE_ARTWORK, 'year created')
            track_field_change(old_instance, instance, 'period_created', ACTION_UPDATE_ARTWORK, 'period created')
            track_field_change(old_instance, instance, 'price', ACTION_UPDATE_ARTWORK, 'price')
            track_field_change(old_instance, instance, 'currency', ACTION_UPDATE_ARTWORK, 'currency')
            track_field_change(
                old_instance,
                instance,
                'is_public_certificate',
                ACTION_UPDATE_ARTWORK,
                'certificate visibility',
            )
            track_field_change(old_instance, instance, 'style_id', ACTION_UPDATE_ARTWORK, 'style')
            track_field_change(old_instance, instance, 'medium_id', ACTION_UPDATE_ARTWORK, 'medium')
            track_field_change(old_instance, instance, 'orientation_id', ACTION_UPDATE_ARTWORK, 'orientation')

            old_audio = old_instance.audio_file
            new_audio = instance.audio_file

            art_title = getattr(instance, 'title', None) or f"Artwork #{getattr(instance, 'pk', '?')}"
            if not old_audio and new_audio:
                inventory_code = instance.inventory_code or 'N/A'
                params = {
                    'title': art_title,
                    'inventory_code': inventory_code,
                }
                template_en = "Added audio file to artwork '{title}' (inventory code: {inventory_code})"
                template_vi = "Đã thêm tệp âm thanh cho tác phẩm '{title}' (mã kiểm kê: {inventory_code})"
                ArtworkLog.objects.create(
                    artwork=instance,
                    user=getattr(instance, '_current_user', None),
                    action_type=ACTION_UPDATE_ARTWORK,
                    content_en=template_en.format(**params),
                    content_vi=template_vi.format(**params),
                    template_en=template_en,
                    template_vi=template_vi,
                    params=params,
                )
            elif old_audio and not new_audio:
                inventory_code = instance.inventory_code or 'N/A'
                params = {
                    'title': art_title,
                    'inventory_code': inventory_code,
                }
                template_en = "Removed audio file from artwork '{title}' (inventory code: {inventory_code})"
                template_vi = "Đã xoá tệp âm thanh khỏi tác phẩm '{title}' (mã kiểm kê: {inventory_code})"
                ArtworkLog.objects.create(
                    artwork=instance,
                    user=getattr(instance, '_current_user', None),
                    action_type=ACTION_UPDATE_ARTWORK,
                    content_en=template_en.format(**params),
                    content_vi=template_vi.format(**params),
                    template_en=template_en,
                    template_vi=template_vi,
                    params=params,
                )
            elif old_audio and new_audio and old_audio != new_audio:
                inventory_code = instance.inventory_code or 'N/A'
                old_filename = old_audio.name if hasattr(old_audio, 'name') else str(old_audio)
                new_filename = new_audio.name if hasattr(new_audio, 'name') else str(new_audio)
                params = {
                    'title': art_title,
                    'inventory_code': inventory_code,
                    'old': old_filename,
                    'new': new_filename,
                }
                template_en = (
                    "Updated audio file of artwork '{title}' (inventory code: {inventory_code}) "
                    "from '{old}' to '{new}'"
                )
                template_vi = (
                    "Đã cập nhật tệp âm thanh của tác phẩm '{title}' (mã kiểm kê: {inventory_code}) "
                    "từ '{old}' thành '{new}'"
                )
                ArtworkLog.objects.create(
                    artwork=instance,
                    user=getattr(instance, '_current_user', None),
                    action_type=ACTION_UPDATE_ARTWORK,
                    content_en=template_en.format(**params),
                    content_vi=template_vi.format(**params),
                    template_en=template_en,
                    template_vi=template_vi,
                    params=params,
                )

        except ArtWork.DoesNotExist:
            pass


@receiver(post_save, sender=ImageArtwork)
def track_image_added(sender, instance, created, **kwargs):
    if created:
        try:
            artwork = instance.artwork
            if artwork and artwork.pk in _DELETING_ARTWORK_IDS:
                return
            if not artwork or not ArtWork.objects.filter(pk=artwork.pk).exists():
                return
            inventory_code = artwork.inventory_code or 'N/A'
            art_title = getattr(artwork, 'title', None) or f"Artwork #{getattr(artwork, 'pk', '?')}"

            user = None
            if hasattr(instance, '_current_user'):
                user = instance._current_user
                artwork._current_user = user

            params = {
                'title': art_title,
                'inventory_code': inventory_code,
            }
            template_en = "Added image to artwork '{title}' (inventory code: {inventory_code})"
            template_vi = "Đã thêm ảnh cho tác phẩm '{title}' (mã kiểm kê: {inventory_code})"
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
        except ArtWork.DoesNotExist:
            return


@receiver(post_delete, sender=ImageArtwork)
def track_image_removed(sender, instance, **kwargs):
    try:
        artwork = instance.artwork
        if artwork and artwork.pk in _DELETING_ARTWORK_IDS:
            return
        if not artwork or not ArtWork.objects.filter(pk=artwork.pk).exists():
            return
        inventory_code = artwork.inventory_code or 'N/A'
        art_title = getattr(artwork, 'title', None) or f"Artwork #{getattr(artwork, 'pk', '?')}"

        user = None
        if hasattr(instance, '_current_user'):
            user = instance._current_user
            artwork._current_user = user

        params = {
            'title': art_title,
            'inventory_code': inventory_code,
        }
        template_en = "Removed image from artwork '{title}' (inventory code: {inventory_code})"
        template_vi = "Đã xoá ảnh khỏi tác phẩm '{title}' (mã kiểm kê: {inventory_code})"
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
    except ArtWork.DoesNotExist:
        return


@receiver(post_save, sender=ArtworkCertificate)
def track_certificate_issued(sender, instance, created, **kwargs):
    if created:
        try:
            artwork = instance.artwork_edition.artwork
            if not artwork or not ArtWork.objects.filter(pk=artwork.pk).exists():
                return
            inventory_code = artwork.inventory_code or 'N/A'
            edition_number = instance.artwork_edition.edition_number
            art_title = getattr(artwork, 'title', None) or f"Artwork #{getattr(artwork, 'pk', '?')}"
            params = {
                'title': art_title,
                'inventory_code': inventory_code,
                'edition_number': edition_number,
            }
            template_en = (
                "Certificate issued for artwork '{title}' (inventory code: {inventory_code}) "
                '(edition: #{edition_number})'
            )
            template_vi = (
                "Đã cấp chứng nhận cho tác phẩm '{title}' (mã kiểm kê: {inventory_code}) "
                '(phiên bản: #{edition_number})'
            )
            ArtworkLog.objects.create(
                artwork=artwork,
                user=instance.issued_by,
                action_type=ACTION_CERTIFICATE_ISSUED,
                content_en=template_en.format(**params),
                content_vi=template_vi.format(**params),
                template_en=template_en,
                template_vi=template_vi,
                params=params,
            )
        except (ArtWork.DoesNotExist, AttributeError):
            return


@receiver(m2m_changed, sender=ArtWork.subjects.through)
def track_subjects_changed(sender, instance, action, pk_set, **kwargs):
    from artwork.models.subject_artwork import SubjectArtwork

    if action in ['post_add', 'post_remove'] and pk_set:
        try:
            if instance and instance.pk in _DELETING_ARTWORK_IDS:
                return
            if not instance or not ArtWork.objects.filter(pk=instance.pk).exists():
                return
            inventory_code = instance.inventory_code or 'N/A'
            art_title = getattr(instance, 'title', None) or f"Artwork #{getattr(instance, 'pk', '?')}"
            subjects = SubjectArtwork.objects.filter(pk__in=pk_set)
            subject_names = ', '.join([subj.name for subj in subjects])

            if action == 'post_add':
                template_en = "Added subjects {subjects} to artwork '{title}' (inventory code: {inventory_code})"
                template_vi = "Đã thêm chủ đề {subjects} vào tác phẩm '{title}' (mã kiểm kê: {inventory_code})"
            else:
                template_en = "Removed subjects {subjects} from artwork '{title}' (inventory code: {inventory_code})"
                template_vi = "Đã xoá chủ đề {subjects} khỏi tác phẩm '{title}' (mã kiểm kê: {inventory_code})"

            params = {
                'subjects': subject_names,
                'title': art_title,
                'inventory_code': inventory_code,
            }

            ArtworkLog.objects.create(
                artwork=instance,
                user=getattr(instance, '_current_user', None),
                action_type=ACTION_UPDATE_ARTWORK,
                content_en=template_en.format(**params),
                content_vi=template_vi.format(**params),
                template_en=template_en,
                template_vi=template_vi,
                params=params,
            )
        except ArtWork.DoesNotExist:
            return


@receiver(m2m_changed, sender=ExhibitionGroup.artworks.through)
def track_artwork_added_to_exhibition(sender, instance, action, pk_set, **kwargs):
    if action == 'post_add' and pk_set:
        exhibition = instance.exhibition
        if exhibition and exhibition.has_ongoing():
            for artwork_id in pk_set:
                try:
                    artwork = ArtWork.objects.get(pk=artwork_id)
                    inventory_code = artwork.inventory_code or 'N/A'
                    art_title = getattr(artwork, 'title', None) or f"Artwork #{getattr(artwork, 'pk', '?')}"
                    exhibition_title = exhibition.title
                    params = {
                        'title': art_title,
                        'inventory_code': inventory_code,
                        'exhibition_title': exhibition_title,
                    }
                    template_en = (
                        "Artwork '{title}' (inventory code: {inventory_code}) added to ongoing exhibition "
                        "('{exhibition_title}')"
                    )
                    template_vi = (
                        "Tác phẩm '{title}' (mã kiểm kê: {inventory_code}) đã được thêm vào triển lãm đang diễn ra "
                        "('{exhibition_title}')"
                    )
                    ArtworkLog.objects.create(
                        artwork=artwork,
                        user=getattr(artwork, '_current_user', None),
                        action_type=ACTION_UPDATE_ARTWORK,
                        content_en=template_en.format(**params),
                        content_vi=template_vi.format(**params),
                        template_en=template_en,
                        template_vi=template_vi,
                        params=params,
                    )
                except ArtWork.DoesNotExist:
                    pass


@receiver(post_save, sender=ArtWork)
def track_artwork_uploaded(sender, instance, created, **kwargs):
    if created:
        try:
            inventory_code = instance.inventory_code or 'N/A'
            art_title = getattr(instance, 'title', None) or f"Artwork #{getattr(instance, 'pk', '?')}"

            user = getattr(instance, '_current_user', None)
            if user is None:
                user = getattr(instance, 'owner', None)

            params = {
                'title': art_title,
                'inventory_code': inventory_code,
            }
            template_en = 'Successfully uploaded artwork {title} (inventory code: {inventory_code})'
            template_vi = 'Tải lên tác phẩm thành công {title} (mã kiểm kê: {inventory_code})'
            ArtworkLog.objects.create(
                artwork=instance,
                user=user,
                action_type=ACTION_ARTWORK_UPLOADED,
                content_en=template_en.format(**params),
                content_vi=template_vi.format(**params),
                template_en=template_en,
                template_vi=template_vi,
                params=params,
            )
        except ArtWork.DoesNotExist:
            pass

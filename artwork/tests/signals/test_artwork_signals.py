from unittest import mock
from types import SimpleNamespace
from datetime import timedelta
from django.utils import timezone

from artwork.signals import (
    _DELETING_ARTWORK_IDS,
    create_artwork_log,
    get_currency_display,
    get_location_display,
    _mark_artwork_deleting,
    _unmark_artwork_deleting,
    track_artwork_deleted,
    track_artwork_changes,
    track_image_added,
    track_image_removed,
    track_certificate_issued,
    track_subjects_changed,
    track_artwork_added_to_exhibition,
    track_artwork_uploaded,
)
from activity_log.models import ArtworkLog
from artwork.factories.artwork import ArtworkFactory
from artwork.factories.image_artwork import ImageArtworkFactory
from artwork.factories.exhibition_group import ExhibitionGroupFactory
from artwork.factories.exhibition import ExhibitionFactory
from artwork.factories.artwork_edition import ArtworkEditionFactory
from artwork.factories.artwork_certificate import ArtworkCertificateFactory
from artwork.factories.style_artwork import StyleArtworkFactory
from artwork.factories.medium_artwork import MediumArtworkFactory
from artwork.factories.orientation_artwork import OrientationArtworkFactory
from artwork.factories.subject_artwork import SubjectArtworkFactory
from core.accounts.factories.user import UserLocationFactory
from core.accounts.factories.user import UserFactory
from core.accounts.tests.api.base_user_test import BaseUserTest
from artwork.models import ArtWork


class ArtworkSignalsTest(BaseUserTest):
    def test_create_artwork_log_early_returns(self):
        count_before = ArtworkLog.objects.count()
        create_artwork_log(None, action_type='artwork_updated')
        self.assertEqual(ArtworkLog.objects.count(), count_before)

    def test_create_artwork_log_swallow_errors(self):
        artwork = ArtworkFactory(owner=self.user)
        with mock.patch('activity_log.models.ArtworkLog.objects.create', side_effect=Exception('x')):
            create_artwork_log(artwork, action_type='artwork_updated', content_en='x')
        self.assertEqual(ArtworkLog.objects.filter(artwork=artwork).count(), 1)

    def test_create_artwork_log_skips_when_marked_deleting(self):
        art = ArtworkFactory(owner=self.user)
        _DELETING_ARTWORK_IDS.add(art.pk)
        create_artwork_log(art, action_type='artwork_updated', content_en='x')
        self.assertFalse(ArtworkLog.objects.filter(artwork=art, action_type='artwork_updated').exists())
        _DELETING_ARTWORK_IDS.discard(art.pk)

    def test_create_artwork_log_exception_on_existence_check(self):
        art = ArtworkFactory(owner=self.user)
        with mock.patch('artwork.signals.ArtWork.objects.filter', side_effect=Exception('boom')):
            create_artwork_log(art, action_type='artwork_updated', content_en='x')
        self.assertFalse(ArtworkLog.objects.filter(artwork=art, action_type='artwork_updated').exists())

    def test_pre_delete_and_post_delete_marks_and_logs(self):
        artwork = ArtworkFactory(owner=self.user)
        artwork._current_user = self.user
        pk = artwork.pk
        self.assertNotIn(pk, _DELETING_ARTWORK_IDS)
        artwork.delete()
        self.assertNotIn(pk, _DELETING_ARTWORK_IDS)
        log = ArtworkLog.objects.filter(content_en__icontains='Deleted artwork').last()
        self.assertIsNotNone(log)
        self.assertIsNone(log.artwork)

    def test_track_field_changes_basic_fields(self):
        loc1 = UserLocationFactory(user=self.user)
        loc2 = UserLocationFactory(user=self.user)
        style1 = StyleArtworkFactory()
        style2 = StyleArtworkFactory()
        medium1 = MediumArtworkFactory()
        medium2 = MediumArtworkFactory()
        orientation1 = OrientationArtworkFactory()
        orientation2 = OrientationArtworkFactory()
        artwork = ArtworkFactory(owner=self.user, status='available', location=loc1, style=style1,
                                 medium=medium1, orientation=orientation1,
                                 inventory_code='INV-100', currency='vnd', is_public_certificate=False,
                                 year_created=2019)
        artwork.title = 'New Title'
        artwork.description = 'New Desc'
        artwork.note = 'New Note'
        artwork.inventory_code = 'INV-200'
        artwork.status = 'sold'
        artwork.location = loc2
        artwork.year_created = 2020
        artwork.period_created = 'Modern'
        artwork.price = 123.45
        artwork.currency = 'usd'
        artwork.is_public_certificate = True
        artwork.style = style2
        artwork.medium = medium2
        artwork.orientation = orientation2
        artwork.save()
        logs = ArtworkLog.objects.all()
        self.assertGreaterEqual(logs.count(), 13)
        texts = ' '.join([(entry.content_en or '') for entry in logs])
        self.assertIn('Changed title', texts)
        self.assertIn('Changed description', texts)
        self.assertIn('Changed note', texts)
        self.assertIn('Changed inventory code', texts)
        self.assertIn('Changed status', texts)
        self.assertIn('Changed location', texts)
        self.assertIn('Changed year created', texts)
        self.assertIn('Changed period created', texts)
        self.assertIn('Changed price', texts)
        self.assertIn('Changed currency', texts)
        self.assertIn('Changed certificate visibility', texts)
        self.assertIn('Changed style', texts)
        self.assertIn('Changed medium', texts)
        self.assertIn('Changed orientation', texts)

    def test_audio_file_add_remove_update(self):
        artwork = ArtworkFactory(owner=self.user, audio_file=None, inventory_code='INV-300', title='Audio Art')
        artwork.audio_file = 'audio1.mp3'
        artwork.save()
        self.assertTrue(ArtworkLog.objects.filter(content_en__icontains='Added audio file').exists())
        last = ArtworkLog.objects.filter(content_en__icontains='Added audio file').order_by('-id').first()
        self.assertIn('Audio Art', last.content_en)
        artwork.audio_file = None
        artwork.save()
        self.assertTrue(ArtworkLog.objects.filter(content_en__icontains='Removed audio file').exists())
        last = ArtworkLog.objects.filter(content_en__icontains='Removed audio file').order_by('-id').first()
        self.assertIn('Audio Art', last.content_en)
        artwork.audio_file = 'audio2.mp3'
        artwork.save()
        artwork.audio_file = 'audio3.mp3'
        artwork.save()
        self.assertTrue(ArtworkLog.objects.filter(content_en__icontains='Updated audio file').exists())
        last = ArtworkLog.objects.filter(content_en__icontains='Updated audio file').order_by('-id').first()
        self.assertIn('Audio Art', last.content_en)

    def test_image_added_and_removed(self):
        artwork = ArtworkFactory(owner=self.user, inventory_code='INV-400', title='Image Art')
        img = ImageArtworkFactory(artwork=artwork)
        self.assertTrue(ArtworkLog.objects.filter(content_en__icontains='Added image').exists())
        last_add = ArtworkLog.objects.filter(content_en__icontains='Added image').order_by('-id').first()
        self.assertIn('Image Art', last_add.content_en)
        img.delete()
        self.assertTrue(ArtworkLog.objects.filter(content_en__icontains='Removed image').exists())
        last_remove = ArtworkLog.objects.filter(content_en__icontains='Removed image').order_by('-id').first()
        self.assertIn('Image Art', last_remove.content_en)

    def test_certificate_issued(self):
        artwork = ArtworkFactory(owner=self.user, inventory_code='INV-500', title='Cert Art')
        edition = ArtworkEditionFactory(artwork=artwork, edition_number=1)
        ArtworkCertificateFactory(artwork_edition=edition, issued_by=self.user)
        self.assertTrue(ArtworkLog.objects.filter(content_en__icontains='Certificate issued').exists())
        last = ArtworkLog.objects.filter(content_en__icontains='Certificate issued').order_by('-id').first()
        self.assertIn('Cert Art', last.content_en)

    def test_subjects_changed_add_and_remove(self):
        artwork = ArtworkFactory(owner=self.user, inventory_code='INV-600', title='Subjects Art')
        s1 = SubjectArtworkFactory()
        s2 = SubjectArtworkFactory()
        artwork.subjects.add(s1.pk, s2.pk)
        self.assertTrue(ArtworkLog.objects.filter(content_en__icontains='subjects').exists())
        last_add = ArtworkLog.objects.filter(content_en__icontains='subjects').order_by('-id').first()
        self.assertIn('Subjects Art', last_add.content_en)
        artwork.subjects.remove(s1.pk)
        self.assertTrue(ArtworkLog.objects.filter(content_en__icontains='subjects').count() >= 2)
        last_remove = ArtworkLog.objects.filter(content_en__icontains='subjects').order_by('-id').first()
        self.assertIn('Subjects Art', last_remove.content_en)

    def test_exhibition_artwork_added_logs_when_ongoing(self):
        exhibition = ExhibitionFactory()
        exhibition.date_start = timezone.now() - timedelta(days=1)
        exhibition.date_end = timezone.now() + timedelta(days=1)
        exhibition.save()
        group = ExhibitionGroupFactory(exhibition=exhibition, artworks=[])
        a = ArtworkFactory(title='Exhibit Art')
        group.artworks.add(a)
        self.assertTrue(
            ArtworkLog.objects.filter(
                artwork=a,
                content_en__icontains='added to ongoing exhibition',
            ).exists(),
        )
        last = (
            ArtworkLog.objects.filter(
                artwork=a,
                content_en__icontains='added to ongoing exhibition',
            )
            .order_by('-id')
            .first()
        )
        self.assertIn('Exhibit Art', last.content_en)

    def test_helpers_currency_and_location(self):
        self.assertEqual(get_currency_display('xxx'), 'xxx')
        self.assertEqual(get_location_display(None), 'N/A')

    def test_mark_unmark_exit_paths(self):
        dummy = SimpleNamespace(pk=None)
        _mark_artwork_deleting(ArtWork, dummy)
        self.assertEqual(len(_DELETING_ARTWORK_IDS), 0)
        _unmark_artwork_deleting(ArtWork, dummy)
        self.assertEqual(len(_DELETING_ARTWORK_IDS), 0)

    def test_track_artwork_deleted_swallow_exceptions(self):
        art = ArtworkFactory(owner=self.user)
        art._current_user = self.user
        with mock.patch('activity_log.models.ArtworkLog.objects.create', side_effect=Exception('x')):
            track_artwork_deleted(ArtWork, art)
        self.assertTrue(True)

    def test_unmark_artwork_deleting_happy_path(self):
        art = ArtworkFactory(owner=self.user)
        _mark_artwork_deleting(ArtWork, art)
        self.assertIn(art.pk, _DELETING_ARTWORK_IDS)
        _unmark_artwork_deleting(ArtWork, art)
        self.assertNotIn(art.pk, _DELETING_ARTWORK_IDS)

    def test_unmark_artwork_deleting_exit_when_not_in_set(self):
        art = ArtworkFactory(owner=self.user)
        self.assertNotIn(art.pk, _DELETING_ARTWORK_IDS)
        _unmark_artwork_deleting(ArtWork, art)
        self.assertNotIn(art.pk, _DELETING_ARTWORK_IDS)

    def test_track_artwork_uploaded_creates_log_with_owner_fallback(self):
        art = ArtworkFactory(owner=self.user, title='Uploaded Art')
        self.assertTrue(
            ArtworkLog.objects.filter(artwork=art, content_en__icontains='Successfully uploaded artwork').exists(),
        )
        log = (
            ArtworkLog.objects.filter(artwork=art, content_en__icontains='Successfully uploaded artwork')
            .order_by('-id')
            .first()
        )
        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.user)

    def test_create_artwork_log_uses_current_user(self):
        art = ArtworkFactory(owner=self.user)
        art._current_user = self.user
        create_artwork_log(art, action_type='artwork_updated', content_en='Hello')
        self.assertTrue(ArtworkLog.objects.filter(artwork=art, user=self.user).exists())

    def test_create_artwork_log_with_non_artwork_instance_swallow_and_user_attr(self):
        dummy = SimpleNamespace(pk=123, _current_user=self.user)
        count_before = ArtworkLog.objects.count()
        create_artwork_log(dummy, action_type='artwork_updated', content_en='x')
        self.assertEqual(ArtworkLog.objects.count(), count_before)

    def test_track_image_removed_with_current_user_path(self):
        art = ArtworkFactory(owner=self.user, title='ImgUser Art')
        img = ImageArtworkFactory(artwork=art)
        img._current_user = self.user
        img.delete()
        self.assertTrue(ArtworkLog.objects.filter(artwork=art, content_en__icontains='Removed image').exists())

    def test_track_artwork_changes_does_not_exist(self):
        art = ArtworkFactory(owner=self.user)
        with mock.patch('artwork.signals.ArtWork.objects.get', side_effect=ArtWork.DoesNotExist()):
            track_artwork_changes(ArtWork, art)
        self.assertTrue(True)

    def test_track_image_added_exits_and_returns_on_missing(self):
        inst = SimpleNamespace(artwork=None)
        track_image_added(object, inst, True)
        self.assertFalse(ArtworkLog.objects.filter(action_type='artwork_updated').exists())

        class Boom:
            @property
            def artwork(self):
                raise ArtWork.DoesNotExist()
        track_image_added(object, Boom(), True)
        self.assertFalse(ArtworkLog.objects.filter(action_type='artwork_updated').exists())
        track_image_added(object, inst, False)
        self.assertFalse(ArtworkLog.objects.filter(action_type='artwork_updated').exists())
        ghost = SimpleNamespace(artwork=SimpleNamespace(pk=999999))
        track_image_added(object, ghost, True)
        self.assertFalse(ArtworkLog.objects.filter(action_type='artwork_updated').exists())

    def test_track_image_removed_returns_and_exception(self):
        inst = SimpleNamespace(artwork=None)
        track_image_removed(object, inst)
        self.assertFalse(ArtworkLog.objects.filter(action_type='artwork_updated').exists())

        class Boom:
            @property
            def artwork(self):
                raise ArtWork.DoesNotExist()
        track_image_removed(object, Boom())
        self.assertFalse(ArtworkLog.objects.filter(action_type='artwork_updated').exists())

    def test_track_image_added_sets_current_user_on_artwork(self):
        artwork = ArtworkFactory(owner=self.user, title='ImgAddUser')
        from artwork.models import ImageArtwork
        img = ImageArtwork(artwork=artwork)
        img._current_user = self.user
        img.save()  # triggers post_save created=True
        self.assertTrue(ArtworkLog.objects.filter(content_en__icontains='Added image', artwork=artwork).exists())

    def test_track_artwork_uploaded_uses_current_user(self):
        other_owner = UserFactory()
        art = ArtworkFactory(owner=other_owner, title='Uploaded CU')
        art._current_user = self.user
        track_artwork_uploaded(ArtWork, art, True)
        log = (
            ArtworkLog.objects.filter(artwork=art, content_en__icontains='Successfully uploaded artwork')
            .order_by('-id')
            .first()
        )
        self.assertIsNotNone(log)
        self.assertEqual(log.user, self.user)

    def test_track_artwork_uploaded_swallow_doesnotexist(self):
        count_before = ArtworkLog.objects.count()

        class Boom:
            def __getattr__(self, name):
                # Bất kỳ truy cập field nào trong handler sẽ ném ArtWork.DoesNotExist
                raise ArtWork.DoesNotExist()

        track_artwork_uploaded(ArtWork, Boom(), True)
        count_after = ArtworkLog.objects.count()
        self.assertEqual(count_before, count_after)

    def test_track_image_added_skips_when_artwork_deleting(self):
        art = ArtworkFactory(owner=self.user)
        count_before = ArtworkLog.objects.count()
        _DELETING_ARTWORK_IDS.add(art.pk)
        inst = SimpleNamespace(artwork=art)
        track_image_added(object, inst, True)
        self.assertEqual(ArtworkLog.objects.count(), count_before)
        _DELETING_ARTWORK_IDS.discard(art.pk)

    def test_track_certificate_issued_returns_and_attr_error(self):

        class DummyEdition:
            def __init__(self, artwork=None, edition_number=1):
                self.artwork = artwork
                self.edition_number = edition_number

        class DummyCert:
            def __init__(self, ed):
                self.artwork_edition = ed
                self.issued_by = None
        ed = DummyEdition(artwork=None)
        cert = DummyCert(ed)
        track_certificate_issued(object, cert, True)

        class NoEdition:
            pass
        track_certificate_issued(object, NoEdition(), True)
        self.assertFalse(ArtworkLog.objects.filter(action_type='certificate_issued').exists())

    def test_subjects_changed_early_and_exception(self):
        track_subjects_changed(object, None, 'post_add', {1})
        art = ArtworkFactory(owner=self.user)
        with mock.patch('artwork.signals.ArtWork.objects.filter', side_effect=ArtWork.DoesNotExist()):
            track_subjects_changed(object, art, 'post_add', {1, 2})
        self.assertTrue(True)

    def test_subjects_changed_skips_when_artwork_deleting(self):
        art = ArtworkFactory(owner=self.user, title='Subjects Skip')
        s = SubjectArtworkFactory()
        count_before = ArtworkLog.objects.count()
        _DELETING_ARTWORK_IDS.add(art.pk)
        track_subjects_changed(object, art, 'post_add', {s.pk})
        track_subjects_changed(object, art, 'post_remove', {s.pk})
        self.assertEqual(ArtworkLog.objects.count(), count_before)
        _DELETING_ARTWORK_IDS.discard(art.pk)

    def test_exhibition_added_missing_artwork_pass(self):
        ex = ExhibitionFactory()
        ex.date_start = ex.date_start.replace(year=2000)
        ex.date_end = ex.date_end.replace(year=3000)
        ex.save()
        group = ExhibitionGroupFactory(exhibition=ex, artworks=[])
        count_before = ArtworkLog.objects.filter(action_type='added_to_exhibition').count()
        track_artwork_added_to_exhibition(object, group, 'post_add', {987654321})
        count_after = ArtworkLog.objects.filter(action_type='added_to_exhibition').count()
        self.assertEqual(count_before, count_after)

    def test_create_artwork_log_returns_when_instance_deleted(self):
        art = ArtworkFactory(owner=self.user)
        pk = art.pk
        art.delete()
        create_artwork_log(art, action_type='update_title', content_en='x')
        self.assertFalse(ArtworkLog.objects.filter(artwork_id=pk).exists())

    def test_track_image_removed_skips_when_artwork_deleting(self):
        art = ArtworkFactory(owner=self.user)
        count_before = ArtworkLog.objects.count()
        _DELETING_ARTWORK_IDS.add(art.pk)
        inst = SimpleNamespace(artwork=art)
        track_image_removed(object, inst)
        self.assertEqual(ArtworkLog.objects.count(), count_before)
        _DELETING_ARTWORK_IDS.discard(art.pk)

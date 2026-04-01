from types import SimpleNamespace

from activity_log.models import ArtworkLog
from artwork.models import SizeArtwork
from artwork.factories.artwork import ArtworkFactory
from core.accounts.tests.api.base_user_test import BaseUserTest
from artwork.serializers.artwork import ArtWorkUpdateFullFieldSerializer, ArtWorkUpdateLessFieldSerializer
from core.accounts.models.user import USER_ROLE


class ArtworkSerializerInternalsTest(BaseUserTest):
    def get_serializer(self):
        ctx = {'request': SimpleNamespace(user=self.user)}
        return ArtWorkUpdateFullFieldSerializer(context=ctx)

    def test_update_size_artwork_no_change_exits(self):
        artwork = ArtworkFactory(owner=self.user)
        artwork.size = SizeArtwork.objects.create(length=10, width=20, height=30, depth=40, weight=50)
        artwork.save()
        serializer = self.get_serializer()
        ArtworkLog.objects.all().delete()
        serializer.update_size_artwork(artwork, {
            'length': 10,
            'width': 20,
            'height': 30,
            'depth': 40,
            'weight': 50,
        })
        self.assertFalse(ArtworkLog.objects.filter(artwork=artwork).exists())

    def test_get_size_display_variations(self):
        serializer = self.get_serializer()
        self.assertEqual(serializer._get_size_display(None), 'N/A')

        class Dummy:
            pass

        d1 = Dummy()
        d1.width = 10
        d1.height = None
        d1.depth = None
        self.assertIn('W:10', serializer._get_size_display(d1))
        d2 = Dummy()
        d2.width = 1
        d2.height = 2.5
        d2.depth = 3
        d2.unit = 'cm'
        out = serializer._get_size_display(d2)
        self.assertIn('W:1', out)
        self.assertIn('H:2.5', out)
        self.assertIn('D:3', out)
        self.assertTrue(out.endswith(' cm'))

    def test_get_size_display_width_height_appended(self):
        serializer = self.get_serializer()

        class Dummy:
            pass

        d = Dummy()
        d.width = 5
        d.height = 7
        out = serializer._get_size_display(d)
        self.assertIn('W:5', out)
        self.assertIn('H:7', out)

    def test_get_size_display_skips_falsy_width_height(self):
        serializer = self.get_serializer()

        class Dummy:
            pass

        d = Dummy()
        d.width = 0
        d.height = None
        out = serializer._get_size_display(d)
        self.assertNotIn('W:0', out)
        self.assertNotIn('H:', out)

    def test_update_image_artwork_sets_current_user_on_add_and_delete(self):
        artwork = ArtworkFactory(owner=self.user)
        artwork._current_user = self.user
        serializer = self.get_serializer()
        serializer.update_image_artwork(artwork, ['img1.png', 'img2.png'])
        from artwork.models import ImageArtwork
        imgs = list(ImageArtwork.objects.filter(artwork=artwork).values_list('image', flat=True))
        self.assertEqual(set(imgs), {'img1.png', 'img2.png'})
        serializer.update_image_artwork(artwork, ['img2.png', 'img3.png'])
        imgs2 = list(ImageArtwork.objects.filter(artwork=artwork).values_list('image', flat=True))
        self.assertEqual(set(imgs2), {'img2.png', 'img3.png'})

    def test_update_image_artwork_propagates_current_user_to_log(self):
        artwork = ArtworkFactory(owner=self.user)
        artwork._current_user = self.user
        serializer = self.get_serializer()
        from activity_log.models import ArtworkLog
        before = ArtworkLog.objects.filter(artwork=artwork, content_en__icontains='Added image').count()
        serializer.update_image_artwork(artwork, ['u1.png'])
        after = ArtworkLog.objects.filter(artwork=artwork, content_en__icontains='Added image').count()
        self.assertEqual(after, before + 1)
        last = ArtworkLog.objects.filter(artwork=artwork, content_en__icontains='Added image').order_by('-id').first()
        self.assertEqual(last.user, self.user)

    def test_update_image_artwork_propagates_current_user_on_delete_log(self):
        artwork = ArtworkFactory(owner=self.user)
        artwork._current_user = self.user
        serializer = self.get_serializer()
        from activity_log.models import ArtworkLog
        serializer.update_image_artwork(artwork, ['a.png', 'b.png'])
        before = ArtworkLog.objects.filter(artwork=artwork, content_en__icontains='Removed image').count()
        serializer.update_image_artwork(artwork, ['b.png'])
        after = ArtworkLog.objects.filter(artwork=artwork, content_en__icontains='Removed image').count()
        self.assertEqual(after, before + 1)
        last = ArtworkLog.objects.filter(artwork=artwork, content_en__icontains='Removed image').order_by('-id').first()
        self.assertEqual(last.user, self.user)

    def test_less_update_propagates_description_to_linked_when_artist(self):
        self.user.role = USER_ROLE.ARTIST
        self.user.save()
        parent = ArtworkFactory(owner=self.user)
        child1 = ArtworkFactory(owner=self.user, linked_artwork=parent)
        child2 = ArtworkFactory(owner=self.user, linked_artwork=parent)
        serializer = ArtWorkUpdateLessFieldSerializer(context={'request': SimpleNamespace(user=self.user)})
        serializer.update(parent, {'description': 'desc123'})
        child1.refresh_from_db()
        child2.refresh_from_db()
        self.assertEqual(child1.description, 'desc123')
        self.assertEqual(child2.description, 'desc123')
